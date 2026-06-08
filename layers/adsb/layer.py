import requests
import concurrent.futures
from core.store import mark_fresh
from layers.adsbdb.layer import ADSBDbLayer

# Instancia global de adsbdb para enriquecimiento
_adsbdb = ADSBDbLayer()

# Flag para activar/desactivar enriquecimiento (puede cambiarse en runtime)
ENRICH_ENABLED = True

# Puntos de consulta para cobertura global
# La API de adsb.lol limita a ~2500nm por consulta, usamos múltiples puntos
GLOBAL_QUERIES = [
    {"lat": 48, "lon": 10, "radius": 2500},   # Europa central
    {"lat": 45, "lon": -30, "radius": 2500},  # Atlántico norte (USA east)
    {"lat": 40, "lon": -100, "radius": 2500}, # USA centro
    {"lat": -15, "lon": -60, "radius": 2500}, # Latinoamérica
    {"lat": 30, "lon": -80, "radius": 2500},  # USA east coast / Caribe
    {"lat": 35, "lon": 140, "radius": 2500},  # Japón / Asia Este
]


def altitude_to_color(altitude_ft):
    """
    Convierte altitud (pies) a color según la barra de altitud visual.
    Esquema de colores:
    - 500 ft: red (#ff3333)
    - 1000 ft: orange (#ff4d00)
    - 2000 ft: yellow (#ff9900)
    - 5000 ft: green (#80ff00)
    - 10000 ft: cyan (#00ccff)
    - 20000 ft: blue (#0066ff)
    - 40000 ft: purple (#6600ff)
    - 60000 ft: magenta (#cc00ff)
    - None: orange (#ff6600) - color de fuente ADS-B
    """
    if altitude_ft is None:
        return "#ff6600"  # Color de fuente ADS-B si no hay altitud

    # Puntos de control (altitud en pies, hex color) - esquema barra de altitud
    points = [
        (500, "#ff3333"),
        (1000, "#ff4d00"),
        (2000, "#ff9900"),
        (5000, "#80ff00"),
        (10000, "#00ccff"),
        (20000, "#0066ff"),
        (40000, "#6600ff"),
        (60000, "#cc00ff"),
    ]

    # Por debajo de 500 ft, usar rojo
    if altitude_ft < 500:
        return "#ff3333"

    # Por encima de 60000 ft, usar magenta
    if altitude_ft >= 60000:
        return "#cc00ff"

    # Encontrar el segmento correcto para interpolación
    for i in range(len(points) - 1):
        alt_low, color_low = points[i]
        alt_high, color_high = points[i + 1]

        if alt_low <= altitude_ft <= alt_high:
            # Interpolación lineal de color
            ratio = (altitude_ft - alt_low) / (alt_high - alt_low)
            return interpolate_color(color_low, color_high, ratio)

    return "#ff3333"  # Default rojo


def interpolate_color(color1, color2, ratio):
    """Interpola entre dos colores hex."""
    # Quitar # si existe
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')

    # Convertir a RGB
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

    # Interpolar
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)

    return f"#{r:02x}{g:02x}{b:02x}"


class ADSBLayer:
    def __init__(self):
        self.id = "adsb"
        self.enabled = True
        # API de adsb.lol es pública y gratuita
        self.base_url = "https://api.adsb.lol/v2"

    def fetch_from_point(self, lat, lon, radius):
        """Obtiene aviones desde un punto específico."""
        try:
            url = f"{self.base_url}/lat/{lat}/lon/{lon}/dist/{radius}"
            res = requests.get(url, timeout=15)
            res.raise_for_status()
            data = res.json()
            return data.get("ac", [])
        except Exception as e:
            print(f"[ADSB] Error fetching from {lat},{lon}: {e}")
            return []

    def fetch(self):
        """Obtiene aviones de múltiples puntos para cobertura global."""
        print(f"[ADSB] Fetching global aircraft data...")

        all_aircraft = []

        # Ejecutar consultas en paralelo para mayor velocidad
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(self.fetch_from_point, q["lat"], q["lon"], q["radius"])
                for q in GLOBAL_QUERIES
            ]
            for future in concurrent.futures.as_completed(futures):
                aircraft = future.result()
                all_aircraft.extend(aircraft)
                print(f"[ADSB] Got {len(aircraft)} aircraft from query")

        print(f"[ADSB] Total raw aircraft: {len(all_aircraft)}")

        # Deduplicar por hex (mismo avión puede aparecer en múltiples consultas)
        seen_hex = set()
        out = []

        for ac in all_aircraft:
            hex_id = ac.get("hex")
            if not hex_id or hex_id in seen_hex:
                continue
            seen_hex.add(hex_id)

            lat = ac.get("lat")
            lon = ac.get("lon")

            # Solo incluir si tiene posición válida
            if lat is None or lon is None:
                continue

            # Convertir a float para evitar errores de comparación
            try:
                lat = float(lat)
                lon = float(lon)
            except (ValueError, TypeError):
                continue

            alt_baro = ac.get("alt_baro")
            # Convertir altitud a entero si es string
            if alt_baro is not None:
                try:
                    alt_baro = int(alt_baro)
                except (ValueError, TypeError):
                    alt_baro = None

            out.append({
                "id": hex_id,  # ICAO24 hex
                "source": self.id,
                "type": "asset",
                "subtype": "aircraft",
                "name": ac.get("flight", "").strip() or hex_id,
                "lat": lat,
                "lon": lon,
                "alt": alt_baro,
                "color": altitude_to_color(alt_baro),
                "heading": ac.get("track"),
                "speed": ac.get("gs"),
                "speed_ias": ac.get("ias"),
                "speed_tas": ac.get("tas"),
                "registration": ac.get("r"),
                "aircraft_type": ac.get("t"),
                "category": ac.get("category"),
                "squawk": ac.get("squawk"),
                "roll": ac.get("roll"),
                "timestamp": ac.get("seen")
            })

        print(f"[ADSB] Points ready after dedup: {len(out)}")

        # Enriquecer datos con adsbdb si está habilitado
        if ENRICH_ENABLED and out:
            print(f"[ADSB] Enriqueneciendo con adsbdb...")
            out = [_adsbdb.enrich_aircraft(ac) for ac in out]
            print(f"[ADSB] Enriquecimiento completado")

        mark_fresh(self.id)
        return out

    def _fallback_data(self):
        """Datos de respaldo cuando la API no responde."""
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "aircraft",
                "name": "ADSB (simulated)",
                "lat": 40.4,
                "lon": -3.7
            }
        ]