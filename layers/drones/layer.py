import requests
from core.store import mark_fresh
import math

# API de ENAIRE - Zonas de vuelo de drones
ENAIRE_API_URL = "https://servais.enaire.es/insignias/rest/services/NSF/Drones_ZG_Aero_V0/MapServer"

# Capas disponibles en el MapServer
CAPAS = {
    "aerodromos": 0,
    "aeromodelismo": 1,
    "zg_aerodromos": 2,
    "zg_eac_fiz": 3,
    "zg_restringidas": 4,
    "zg_rvf": 5,
    "avisos": 6
}

# Colores para cada tipo de zona
COLORES = {
    "aerodromos": "#ffaa00",
    "aeromodelismo": "#a855f7",
    "zg_aerodromos": "#22c55e",
    "zg_eac_fiz": "#3b82f6",
    "zg_restringidas": "#ef4444",
    "zg_rvf": "#eab308",
    "avisos": "#f97316"
}

def convertir_3857_a_4326(x, y):
    """Convierte coordenadas EPSG:3857 (Web Mercator) a EPSG:4326 (lat/lon)"""
    lon = (x / 20037508.34) * 180
    lat = (y / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lat, lon

def convertir_anillo_a_coords(ring):
    """Convierte un anillo de polígono EPSG:3857 a coordenadas EPSG:4326"""
    coords = []
    for point in ring:
        lat, lon = convertir_3857_a_4326(point[0], point[1])
        coords.append([lat, lon])
    # Cerrar el polígono si no lo está
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords

def convertir_geom_a_geojson(geom):
    """Convierte geometría del MapServer de ENAIRE a formato GeoJSON"""
    if "x" in geom and "y" in geom:
        # Es un punto
        lat, lon = convertir_3857_a_4326(geom["x"], geom["y"])
        return {"type": "Point", "coordinates": [lon, lat]}
    elif "rings" in geom:
        # Es un polígono
        rings = []
        for ring in geom["rings"]:
            rings.append(convertir_anillo_a_coords(ring))
        if len(rings) == 1:
            return {"type": "Polygon", "coordinates": rings[0]}
        else:
            return {"type": "MultiPolygon", "coordinates": rings}
    return None

class DronesLayer:
    def __init__(self):
        self.id = "drones"
        self.enabled = True

    def fetch(self):
        out = []
        zonas_poligonos = []
        try:
            # Consultar cada capa del MapServer
            for nombre_capa, id_capa in CAPAS.items():
                url = f"{ENAIRE_API_URL}/{id_capa}/query"
                params = {
                    "where": "1=1",
                    "outFields": "*",
                    "f": "json",
                    "returnGeometry": "true"
                }
                try:
                    res = requests.get(url, params=params, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        for feature in data.get("features", []):
                            attrs = feature.get("attributes", {})
                            geom = feature.get("geometry", {})

                            # Extraer nombre/identificador
                            nombre = attrs.get("IDENT_TXT") or attrs.get("NOMBRE") or attrs.get("NAME") or f"{nombre_capa}_{attrs.get('OBJECTID', '')}"

                            # Convertir geometría a GeoJSON
                            geojson_geom = convertir_geom_a_geojson(geom)
                            if not geojson_geom:
                                continue

                            # Determinar subtype basado en la capa
                            subtype_map = {
                                "aerodromos": "aerodromo",
                                "aeromodelismo": "aeromodelismo",
                                "zg_aerodromos": "zona_aerodromo",
                                "zg_eac_fiz": "espacio_controlado",
                                "zg_restringidas": "zona_restringida",
                                "zg_rvf": "vuelo_fotografico",
                                "avisos": "aviso"
                            }

                            # Extraer información adicional relevante
                            info_extra = {}
                            for key in attrs.keys():
                                if key not in ['OBJECTID', 'SHAPE', 'SHAPE_LENGTH', 'SHAPE_AREA']:
                                    info_extra[key] = attrs[key]

                            zona = {
                                "source": self.id,
                                "type": "zone",
                                "subtype": subtype_map.get(nombre_capa, "zona_drone"),
                                "name": nombre,
                                "geometry": geojson_geom,
                                "capa": nombre_capa,
                                "color": COLORES.get(nombre_capa, "#ffffff"),
                                "info": info_extra
                            }

                            # Si es un punto, añadir lat/lon también
                            if geojson_geom["type"] == "Point":
                                zona["lat"] = geojson_geom["coordinates"][1]
                                zona["lon"] = geojson_geom["coordinates"][0]

                            zonas_poligonos.append(zona)
                except Exception as e:
                    print(f"[DRONES] Error consultando capa {nombre_capa}: {e}")
                    continue

            # Limitar el número de zonas para no saturar
            out = zonas_poligonos[:150]
            mark_fresh(self.id)
            return out

        except Exception as e:
            print(f"[DRONES] Error general: {e}")
            mark_fresh(self.id)
            return []