from layers.n2yo.layer import N2YOLayer
from layers.enaire.layer import EnaireLayer
from layers.adsb.layer import ADSBLayer
from layers.downdetector.layer import DowndetectorLayer
from layers.airnavradar.layer import AirNavRadarLayer
from layers.ourairports.layer import OurAirportsLayer
from layers.geamap.layer import GeaMapLayer
from layers.thousandeyes.layer import ThousandEyesLayer
from layers.races.layer import RacesLayer
from layers.aisstream.layer import AISStreamLayer
from layers.drones.layer import DronesLayer
from layers.celestrak.layer import CelestrakLayer
from layers.adsbdb.layer import ADSBDbLayer
from core.store import active_layers, set_layer_active

class LayerRegistry:
    def __init__(self):
        self.layers = {
            "n2yo": N2YOLayer(),
            "celestrak": CelestrakLayer(),
            "enaire": EnaireLayer(),
            "adsb": ADSBLayer(),
            "downdetector": DowndetectorLayer(),
            "airnavradar": AirNavRadarLayer(),
            "ourairports": OurAirportsLayer(),
            "geamap": GeaMapLayer(),
            "thousandeyes": ThousandEyesLayer(),
            "races": RacesLayer(),
            "aisstream": AISStreamLayer(),
            "drones": DronesLayer(),
            "adsbdb": ADSBDbLayer(),  # Capa de enriquecimiento (deshabilitada por defecto)
        }
        # Deshabilitar adsbdb por defecto - es capa de enriquecimiento, no fuente de datos
        self.layers["adsbdb"].enabled = False

    def get_layers(self):
        return [l for l in self.layers.values() if l.enabled]

    def get_all_layers(self):
        """Get all layers (enabled and disabled)."""
        return list(self.layers.values())

    def enable(self, name):
        if name in self.layers:
            self.layers[name].enabled = True
            set_layer_active(name, True)

    def disable(self, name):
        if name in self.layers:
            self.layers[name].enabled = False
            set_layer_active(name, False)

    def toggle(self, name):
        if name in self.layers:
            self.layers[name].enabled = not self.layers[name].enabled
            set_layer_active(name, self.layers[name].enabled)

    def get_layer_info(self, name):
        """Get information about a specific layer."""
        if name not in self.layers:
            return None
        layer = self.layers[name]
        return {
            "id": layer.id,
            "enabled": layer.enabled
        }

