from core.store import mark_fresh

class AirNavRadarLayer:
    def __init__(self):
        self.id = "airnavradar"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        # Simulated AirNav Radar data
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "radar",
                "name": "Barcelona Radar",
                "lat": 41.2974,
                "lon": 2.0833
            },
            {
                "source": self.id,
                "type": "asset",
                "subtype": "radar",
                "name": "Madrid Radar",
                "lat": 40.4936,
                "lon": -3.5668
            }
        ]