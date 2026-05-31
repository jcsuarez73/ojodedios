from core.store import mark_fresh

class DowndetectorLayer:
    def __init__(self):
        self.id = "downdetector"
        self.enabled = True

    def fetch(self):
        mark_fresh(self.id)
        return [
            {
                "source": self.id,
                "type": "event",
                "subtype": "service_outage",
                "name": "WhatsApp (simulado)"
            },
            {
                "source": self.id,
                "type": "event",
                "subtype": "service_outage",
                "name": "Google (simulado)"
            }
        ]
