from core.store import mark_fresh

class RacesLayer:
    def __init__(self):
        self.id = "races"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "event",
                "subtype": "race",
                "name": "Circuit de Barcelona-Catalunya",
                "lat": 41.5700,
                "lon": 2.2611
            },
            {
                "source": self.id,
                "type": "event",
                "subtype": "race",
                "name": "Jarama Race Track",
                "lat": 40.6297,
                "lon": -3.5831
            }
        ]