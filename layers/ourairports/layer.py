from core.store import mark_fresh

class OurAirportsLayer:
    def __init__(self):
        self.id = "ourairports"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "poi",
                "subtype": "airport",
                "name": "Adolfo Suárez Madrid-Barajas",
                "lat": 40.4936,
                "lon": -3.5668
            },
            {
                "source": self.id,
                "type": "poi",
                "subtype": "airport",
                "name": "Barcelona-El Prat",
                "lat": 41.2974,
                "lon": 2.0833
            },
            {
                "source": self.id,
                "type": "poi",
                "subtype": "airport",
                "name": "Palma de Mallorca",
                "lat": 39.5517,
                "lon": 2.5768
            }
        ]