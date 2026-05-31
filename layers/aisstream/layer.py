from core.store import mark_fresh

class AISStreamLayer:
    def __init__(self):
        self.id = "aisstream"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "asset",
                "subtype": "vessel",
                "name": "MSC GULS",
                "lat": 41.2825,
                "lon": 2.3156
            },
            {
                "source": self.id,
                "type": "asset",
                "subtype": "vessel",
                "name": "Port of Valencia",
                "lat": 39.4439,
                "lon": -0.3347
            }
        ]