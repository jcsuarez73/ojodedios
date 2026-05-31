from core.store import mark_fresh

class ThousandEyesLayer:
    def __init__(self):
        self.id = "thousandeyes"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "network",
                "subtype": "test_point",
                "name": "Madrid Node",
                "lat": 40.4167,
                "lon": -3.7037
            },
            {
                "source": self.id,
                "type": "network",
                "subtype": "test_point",
                "name": "Barcelona Node",
                "lat": 41.3851,
                "lon": 2.1734
            }
        ]