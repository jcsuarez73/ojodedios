from core.store import mark_fresh

class GeaMapLayer:
    def __init__(self):
        self.id = "geamap"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "poi",
                "subtype": "geological",
                "name": "Teide Volcano",
                "lat": 28.2723,
                "lon": -16.6396
            },
            {
                "source": self.id,
                "type": "poi",
                "subtype": "geological",
                "name": "Caldera de Taburiente",
                "lat": 28.7183,
                "lon": -17.7656
            }
        ]