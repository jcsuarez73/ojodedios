import requests
import math
from datetime import datetime, timedelta
from sgp4.api import Satrec, jday
from core.store import mark_fresh


# Satélites populares a trackear (IDs válidos en Celestrak)
SATELLITE_CATALOG = {
    25544: "ISS (ZARYA)",
    37849: "AJISAI",
    42740: "TESAT",
    43013: "STARLINK-1007",
    44923: "STARLINK-1547",
    40071: "X-37B",
}


class CelestrakLayer:
    def __init__(self):
        self.id = "celestrak"
        self.enabled = True
        self.base_url = "https://celestrak.org/NORAD/elements/gp.php"
        # Satélites a trackear - solo IDs que existen en Celestrak
        self.track_ids = [25544, 37849]  # ISS, AJISAI
        # Cache de TLEs
        self.tle_cache = {}
        self.cache_time = None
        self.cache_ttl = timedelta(hours=1)

    def _fetch_tle(self, sat_id):
        """Obtiene TLE para un satélite específico."""
        try:
            url = f"{self.base_url}?CATNR={sat_id}&FORMAT=tle"
            res = requests.get(url, timeout=10)
            if res.status_code == 404:
                print(f"[CELESTRAK] Satellite {sat_id} not found in Celestrak")
                return None
            res.raise_for_status()
            lines = res.text.strip().split('\n')
            # Celestrak puede devolver 2 o 3 líneas:
            # 2 líneas: solo TLE
            # 3 líneas: nombre + TLE1 + TLE2
            if len(lines) == 3:
                name = lines[0].strip()
                tle_line1 = lines[1].strip()
                tle_line2 = lines[2].strip()
            elif len(lines) == 2:
                name = f"SAT{sat_id}"
                tle_line1 = lines[0].strip()
                tle_line2 = lines[1].strip()
            else:
                return None

            # Verificar formato básico de TLE
            if not tle_line1.startswith('1 ') or not tle_line2.startswith('2 '):
                print(f"[CELESTRAK] Invalid TLE format for {sat_id}")
                return None

            return {'name': name, 'line1': tle_line1, 'line2': tle_line2}
        except Exception as e:
            print(f"[CELESTRAK] Error fetching TLE for {sat_id}: {e}")
            return None

    def _compute_position(self, satrec, minutes_offset=0):
        """Calcula posición del satélite usando SGP4."""
        try:
            # Obtener tiempo actual + offset
            now = datetime.utcnow() + timedelta(minutes=minutes_offset)
            jd, fr = jday(now.year, now.month, now.day,
                          now.hour, now.minute, now.second)

            error, r, v = satrec.sgp4(jd, fr)

            if error == 0:  # Éxito
                # Convertir posición a lat/lon (simplificado)
                # r está en km en coordenadas ECI
                x, y, z = r  # km

                # Conversión aproximada a lat/lon (asumiendo Tierra esférica)
                R_earth = 6371  # km

                # Distancia desde el centro de la Tierra
                dist = math.sqrt(x*x + y*y + z*z)

                # Normalizar
                x_norm = x / R_earth
                y_norm = y / R_earth
                z_norm = z / R_earth

                # Calcular lat/lon
                lon = math.atan2(y_norm, x_norm) * 180 / math.pi
                lat = math.asin(z_norm) * 180 / math.pi

                return {
                    'lat': lat,
                    'lon': lon,
                    'alt_km': dist - R_earth
                }
            return None
        except Exception as e:
            print(f"[CELESTRAK] Error computing position: {e}")
            return None

    def fetch(self):
        """Obtiene posiciones de satélites desde Celestrak."""
        try:
            # Verificar cache
            now = datetime.utcnow()
            if self.cache_time and (now - self.cache_time) < self.cache_ttl:
                # Usar cache
                pass
            else:
                # Refresh TLEs
                self.tle_cache = {}
                for sat_id in self.track_ids:
                    tle = self._fetch_tle(sat_id)
                    if tle:
                        self.tle_cache[sat_id] = tle
                self.cache_time = now

            out = []

            # Calcular posiciones para cada satélite
            for sat_id, tle in self.tle_cache.items():
                try:
                    # Usar el método de clase twoline2rv
                    sat = Satrec.twoline2rv(tle['line1'], tle['line2'])

                    # Obtener posición actual y predicciones (cada 5 min por 1 hora)
                    for offset in [0, 5, 10, 15, 20, 25, 30]:
                        pos = self._compute_position(sat, offset)
                        if pos and -90 <= pos['lat'] <= 90 and -180 <= pos['lon'] <= 180:
                            out.append({
                                "source": self.id,
                                "type": "asset",
                                "subtype": "satellite",
                                "name": tle['name'],
                                "sat_id": sat_id,
                                "lat": pos['lat'],
                                "lon": pos['lon'],
                                "alt_km": pos.get('alt_km', 0),
                                "minutes_offset": offset,
                                "timestamp": (now + timedelta(minutes=offset)).isoformat()
                            })

                except Exception as e:
                    print(f"[CELESTRAK] Error processing {sat_id}: {e}")
                    continue

            print(f"[CELESTRAK] Points ready: {len(out)}")
            mark_fresh(self.id)
            return out

        except Exception as e:
            print(f"[CELESTRAK] Error: {e}")
            return self._fallback_data()

    def _fallback_data(self):
        """Datos de respaldo cuando la API no responde."""
        print("[CELESTRAK] Using fallback data")
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "satellite",
                "name": "ISS (celestrak fallback)",
                "lat": 40.4,
                "lon": -3.7
            }
        ]