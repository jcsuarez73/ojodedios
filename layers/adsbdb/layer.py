"""
Capa adsbdb - API de enriquecimiento de datos de aviones
https://github.com/mrjackwills/adsbdb

Esta capa NO es una fuente de datos primaria.
Sirve para enriquecer datos de otras capas (adsb, enaire) con:
- Datos del avión (matrícula, tipo, fabricante, operador)
- Fotos del avión
- Rutas de vuelo (origen/destino por callsign)
"""

import requests
import time
from typing import List, Dict, Any, Optional
from core.store import mark_fresh

ADSBCDB_API = "https://api.adsbdb.com/v0"

# Cache simple: {icao24: (data, timestamp)}
_cache: Dict[str, tuple] = {}
CACHE_TTL = 3600  # 1 hora


class ADSBDbLayer:
    def __init__(self):
        self.id = "adsbdb"
        self.enabled = True  # Enabled pero no fetch por defecto

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Esta capa no fetch datos.
        Retorna lista vacía - usar get_aircraft_details() directamente.
        """
        return []

    def _get_cached(self, icao24: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos del cache si no han expirado."""
        if icao24 in _cache:
            data, timestamp = _cache[icao24]
            if time.time() - timestamp < CACHE_TTL:
                return data
        return None

    def _set_cache(self, icao24: str, data: Dict[str, Any]):
        """Guarda datos en cache."""
        _cache[icao24] = (data, time.time())

    def get_aircraft_details(self, icao24: str) -> Dict[str, Any]:
        """
        Obtiene detalles de un avión por su MODE-S hex.
        Ejemplo: get_aircraft_details("4cadbc")
        """
        # Limpiar el icao24 (quitar espacios, mayúsculas)
        icao24 = icao24.strip().lower()

        # Verificar cache
        cached = self._get_cached(icao24)
        if cached:
            return cached

        url = f"{ADSBCDB_API}/aircraft/{icao24}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # La API devuelve {response: {aircraft: {...}}}}
                response = r.json().get("response", {})
                data = response.get("aircraft", {})
                self._set_cache(icao24, data)
                return data
        except Exception as e:
            print(f"[adsbdb] Error fetching {icao24}: {e}")

        return {}

    def get_aircraft_by_registration(self, registration: str) -> Dict[str, Any]:
        """
        Obtiene detalles de un avión por su matrícula.
        Ejemplo: get_aircraft_by_registration("EC-LZX")
        """
        registration = registration.strip().upper().replace("-", "")

        url = f"{ADSBCDB_API}/aircraft/{registration}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                response = r.json().get("response", {})
                return response.get("aircraft", {})
        except Exception as e:
            print(f"[adsbdb] Error fetching {registration}: {e}")

        return {}

    def get_route_by_callsign(self, callsign: str) -> Dict[str, Any]:
        """
        Obtiene información de ruta de vuelo por callsign.
        Ejemplo: get_route_by_callsign("IBE1234")
        """
        callsign = callsign.strip().upper()

        url = f"{ADSBCDB_API}/callsign/{callsign}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                response = r.json().get("response", {})
                # callsign puede devolver varios resultados
                if isinstance(response, list) and len(response) > 0:
                    return response[0]
                return response
        except Exception as e:
            print(f"[adsbdb] Error fetching callsign {callsign}: {e}")

        return {}

    def get_airline(self, code: str) -> Dict[str, Any]:
        """
        Obtiene información de aerolinea por código ICAO o IATA.
        Ejemplo: get_airline("IBE") o get_airline("IB")
        """
        code = code.strip().upper()

        url = f"{ADSBCDB_API}/airline/{code}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                response = r.json().get("response", {})
                # airline devuelve un array
                if isinstance(response, list) and len(response) > 0:
                    return response[0]
                return response
        except Exception as e:
            print(f"[adsbdb] Error fetching airline {code}: {e}")

        return {}

    def enrich_aircraft(self, aircraft_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece un objeto de avión con datos de adsbdb.
        Añade: registration, type, manufacturer, operator, owner, country, photos

        Uso:
            from layers.adsbdb.layer import ADSBDbLayer
            adsbdb = ADSBDbLayer()

            for plane in adsb_planes:
                plane = adsbdb.enrich_aircraft(plane)
        """
        icao24 = aircraft_data.get("id")
        if not icao24:
            return aircraft_data

        details = self.get_aircraft_details(icao24)
        if not details:
            return aircraft_data

        # Añadir datos enrichidos (campos de la API adsbdb)
        aircraft_data["registration"] = details.get("registration")
        aircraft_data["aircraft_type"] = details.get("type")
        aircraft_data["manufacturer"] = details.get("manufacturer")
        aircraft_data["operator"] = details.get("registered_owner")
        aircraft_data["operator_flag"] = details.get("registered_owner_operator_flag_code")
        aircraft_data["owner"] = details.get("registered_owner")
        aircraft_data["country"] = details.get("registered_owner_country_name")
        aircraft_data["country_iso"] = details.get("registered_owner_country_iso_name")
        aircraft_data["photo_url"] = details.get("url_photo")
        aircraft_data["photo_thumbnail"] = details.get("url_photo_thumbnail")

        return aircraft_data

    def enrich_aircraft_list(self, aircraft_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enriquece una lista de aviones.
        OJO: Hace una llamada API por avión - usar con precaución.
        """
        return [self.enrich_aircraft(ac) for ac in aircraft_list]


# Instancia global para usar directamente
_enricher = ADSBDbLayer()


def enrich_aircraft(aircraft_data: Dict[str, Any]) -> Dict[str, Any]:
    """Función helper para enrich aircraft."""
    return _enricher.enrich_aircraft(aircraft_data)


def get_aircraft_details(icao24: str) -> Dict[str, Any]:
    """Función helper para obtener detalles."""
    return _enricher.get_aircraft_details(icao24)


def get_route_by_callsign(callsign: str) -> Dict[str, Any]:
    """Función helper para obtener ruta."""
    return _enricher.get_route_by_callsign(callsign)