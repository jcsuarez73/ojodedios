import requests
import os
from core.store import mark_fresh


class N2YOLayer:
    def __init__(self):
        self.id = "n2yo"
        self.enabled = True
        # API key del usuario configurada directamente
        self.api_key = os.environ.get("N2YO_API_KEY", "J5R39K-F2UC89-6FZAGX-5QM9")
        self.sat_id = 25544  # ISS

    def fetch(self):
        try:
            # 🔥 PARAMETROS CORRECTOS
            url = f"https://api.n2yo.com/rest/v1/satellite/positions/{self.sat_id}/40.4/-3.7/100/10/?apiKey={self.api_key}"
            print(f"[N2YO] Requesting: {url}")

            res = requests.get(url, timeout=5)
            data = res.json()

            # ❌ ERROR API
            if data.get("error"):
                print(f"[N2YO] API Error: {data.get('error')}")
                return self._fallback_data()

            out = []

            positions = data.get("positions", [])
            print(f"[N2YO] Positions received: {len(positions)}")

            for p in positions:
                lat = p.get("satlatitude")
                lon = p.get("satlongitude")

                # 🔥 VALIDACIÓN CRÍTICA
                if lat is None or lon is None:
                    continue

                out.append({
                    "source": self.id,
                    "type": "asset",
                    "subtype": "satellite",
                    "name": "ISS",
                    "lat": lat,
                    "lon": lon,
                    "timestamp": p.get("timestamp")
                })

            print(f"[N2YO] Points ready: {len(out)}")

            mark_fresh(self.id)
            return out

        except Exception as e:
            print(f"[N2YO] Error: {e}")
            return self._fallback_data()

    def _fallback_data(self):
        """Datos de respaldo cuando la API no responde."""
        print("[N2YO] Using fallback data")

        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "satellite",
                "name": "ISS (simulated)",
                "lat": 40.4,
                "lon": -3.7
            }
        ]