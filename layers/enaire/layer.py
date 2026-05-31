import requests
import os
from core.store import mark_fresh
from layers.adsbdb.layer import ADSBDbLayer

# Instancia global de adsbdb para enriquecimiento
_adsbdb = ADSBDbLayer()

# Flag para activar/desactivar enriquecimiento
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

    if altitude_ft < 500:
        return hsl_to_hex(1, 100, 40)

    if altitude_ft >= 60000:
        return hsl_to_hex(360, 100, 40)

    for i in range(len(points) - 1):
        alt_low, hue_low = points[i]
        alt_high, hue_high = points[i + 1]

        if alt_low <= altitude_ft <= alt_high:
            ratio = (altitude_ft - alt_low) / (alt_high - alt_low)
            hue = hue_low + ratio * (hue_high - hue_low)
            return hsl_to_hex(int(hue), 100, 40)

    return hsl_to_hex(1, 100, 40)


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


class EnaireLayer:
    def __init__(self):
        self.id = "enaire"
        self.enabled = True
        # OpenSky no requiere API key para datos públicos básicos
        # Pero tiene rate limit. Para mayor límite, obtener credenciales en OpenSky
        self.username = os.environ.get("OPENSKY_USERNAME", None)
        self.password = os.environ.get("OPENSKY_PASSWORD", None)

    def fetch(self):
        try:
            url = "https://opensky-network.org/api/states/all?lamin=36&lomin=-9&lamax=43&lomax=3"

            # Si hay credenciales, las usamos para mayor rate limit
            if self.username and self.password:
                res = requests.get(url, auth=(self.username, self.password))
            else:
                res = requests.get(url)

            # Rate limit excedido
            if res.status_code == 429:
                print("[ENAIRE] Rate limit exceeded. Using fallback data.")
                return self._fallback_data()

            res.raise_for_status()
            data = res.json()

            out = []
            for s in data.get("states", [])[:80]:
                if s[5] and s[6]:  # lon, lat
                    # s[7] = alt_baro (pies), s[15] = geometric altitude
                    alt_baro = s[7]  # altitud en pies

                    out.append({
                        "id": s[0],   # ICAO24 hex
                        "source": self.id,
                        "type": "asset",
                        "subtype": "aircraft",
                        "name": s[1] or s[0],  # callsign o icao24
                        "lat": s[6],
                        "lon": s[5],
                        "alt": alt_baro,
                        "color": altitude_to_color(alt_baro)
                    })

            # Enriquecer datos con adsbdb si está habilitado
            if ENRICH_ENABLED:
                print(f"[ENAIRE] Enriqueneciendo con adsbdb...")
                out = [_adsbdb.enrich_aircraft(ac) for ac in out]
                print(f"[ENAIRE] Enriquecimiento completado")

            mark_fresh(self.id)
            return out
        except Exception as e:
            print(f"[ENAIRE] Error: {e}")
            return self._fallback_data()

    def _fallback_data(self):
        """Datos de respaldo cuando la API no responde."""
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "aircraft",
                "name": "Aircraft (simulated)",
                "lat": 40.4,
                "lon": -3.7
            }
        ]
