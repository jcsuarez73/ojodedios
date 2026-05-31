import requests
from core.store import mark_fresh
from layers.adsbdb.layer import ADSBDbLayer

# Instancia global de adsbdb para enriquecimiento
_adsbdb = ADSBDbLayer()

# Flag para activar/desactivar enriquecimiento (puede cambiarse en runtime)
ENRICH_ENABLED = True


def altitude_to_color(altitude_ft):
    """
    Convierte altitud (pies) a color según esquema ADS-B.lol.
    Esquema exacto:
    - 500 ft: red (hue 1)
    - 1000 ft: orange (hue 30)
    - 2000 ft: yellow (hue 60)
    - 5000 ft: green (hue 120)
    - 10000 ft: cyan (hue 180)
    - 20000 ft: blue (hue 240)
    - 40000 ft: magenta (hue 300)
    - 60000 ft+: red (hue 360)
    """
    if altitude_ft is None:
        return "#666666"  # Gris si no hay altitud

    # Puntos de control (altitud en pies, hue) - esquema adsb.lol
    points = [
        (500, 1),
        (1000, 30),
        (2000, 60),
        (5000, 120),
        (10000, 180),
        (20000, 240),
        (40000, 300),
        (60000, 360),
    ]

    # Por debajo de 500 ft, usar rojo
    if altitude_ft < 500:
        return hsl_to_hex(1, 100, 40)

    # Por encima de 60000 ft, usar rojo (ciclo completo)
    if altitude_ft >= 60000:
        return hsl_to_hex(360, 100, 40)

    # Encontrar el segmento correcto para interpolación
    for i in range(len(points) - 1):
        alt_low, hue_low = points[i]
        alt_high, hue_high = points[i + 1]

        if alt_low <= altitude_ft <= alt_high:
            # Interpolación lineal
            ratio = (altitude_ft - alt_low) / (alt_high - alt_low)
            hue = hue_low + ratio * (hue_high - hue_low)
            return hsl_to_hex(int(hue), 100, 40)

    return hsl_to_hex(1, 100, 40)  # Default rojo


def hsl_to_hex(h, s=100, l=40):
    """Convierte HSL a hex color."""
    s /= 100
    l /= 100
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    r = int((r + m) * 255)
    g = int((g + m) * 255)
    b = int((b + m) * 255)

    return f"#{r:02x}{g:02x}{b:02x}"


class ADSBLayer:
    def __init__(self):
        self.id = "adsb"
        self.enabled = True
        # API de adsb.lol es pública y gratuita
        self.base_url = "https://api.adsb.lol/v2"

    def fetch(self):
        try:
            # Obtener todos los aviones con posición
            # Usamos punto con radio (en millas náuticas)
            # lat=40, lon=-4, radius=300 (nm) = cobertura de España
            url = f"{self.base_url}/point/40/-4/300"
            print(f"[ADSB] Requesting: {url}")

            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()

            out = []
            aircraft = data.get("ac", [])

            print(f"[ADSB] Aircraft received: {len(aircraft)}")

            for ac in aircraft:
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

                # Filtrar solo España y cercanías (lat 36-43, lon -18 to 5)
                # Incluye Atlántico hasta-Azores/Madeira
                if not (36 <= lat <= 43 and -18 <= lon <= 5):
                    continue

                alt_baro = ac.get("alt_baro")
                # Convertir altitud a entero si es string
                if alt_baro is not None:
                    try:
                        alt_baro = int(alt_baro)
                    except (ValueError, TypeError):
                        alt_baro = None

                out.append({
                    "id": ac.get("hex"),  # ICAO24 hex
                    "source": self.id,
                    "type": "asset",
                    "subtype": "aircraft",
                    "name": ac.get("flight", "").strip() or ac.get("hex", ""),
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

            print(f"[ADSB] Points ready: {len(out)}")

            # Enriquecer datos con adsbdb si está habilitado
            if ENRICH_ENABLED:
                print(f"[ADSB] Enriqueneciendo con adsbdb...")
                out = [_adsbdb.enrich_aircraft(ac) for ac in out]
                print(f"[ADSB] Enriquecimiento completado")

            mark_fresh(self.id)
            return out

        except Exception as e:
            print(f"[ADSB] Error: {e}")
            return self._fallback_data()

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