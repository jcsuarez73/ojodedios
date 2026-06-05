import requests
from core.store import mark_fresh
import math

# API de ENAIRE - MapServer V0 (capas principales)
ENAIRE_MAP_SERVER = "https://servais.enaire.es/insignias/rest/services/NSF/Drones_ZG_Aero_V0/MapServer"

# API de ENAIRE - FeatureServer (capas adicionales)
ENAIRE_FEATURE_SERVER = "https://servais.enaire.es/insignia/rest/services/NSF_SRV/SRV_UAS_ZG_V1/FeatureServer"

# Capas disponibles en el MapServer V0
# ID 0: AERODROMOS (punto)
# ID 1: ZG_EAC_FIZ (polígono) - Espacio Controlado
# ID 2: AVISOS (polígono) - NOTAM
# ID 3: ZG_RVF (polígono) - Restringido Vuelo Fotográfico
# ID 4: AEROMODELISMO (punto)
# ID 6: ZG_Aeródromos (polígono)
# ID 10: ZG_Restringidas (polígono)
CAPAS_MAP = {
    "aerodromos": 0,
    "zg_eac_fiz": 1,
    "notam": 2,
    "zg_rvf": 3,
    "aeromodelismo": 4,
    "zg_aerodromos": 6,
    "zg_restringidas": 10
}

# Capas adicionales del FeatureServer
# ID 0: ZGUAS_Infraestructuras (polígono) - Zonas de infraestructuras
# ID 2: ZGUAS_Aero (polígono) - Aeródromos
# ID 3: ZGUAS_Urbano (polígono) - Zonas urbanas
CAPAS_FEATURE = {
    "zg_infraestructuras": 0,
    "zg_aero": 2,
    "zg_urbano": 3
}

# Combinar todas las capas
CAPAS = {**CAPAS_MAP, **CAPAS_FEATURE}

# Mapeo de IDs a nombres legibles (MapServer)
NOMBRE_CAPA = {
    0: "Aeródromos",
    1: "ZG EAC/FIZ",
    2: "NOTAM",
    3: "ZG RVF (Vuelo Fotográfico)",
    4: "Aeromodelismo",
    6: "ZG Aeródromos",
    10: "ZG Restringidas"
}

# Mapeo de IDs a nombres legibles (FeatureServer)
NOMBRE_CAPA_FEATURE = {
    0: "ZG Infraestruturas",
    2: "ZG Aero",
    3: "ZG Urbano"
}

# Subtypes para el frontend
SUBTYPE_CAPA = {
    0: "aerodromo",
    1: "espacio_controlado",
    2: "notam",
    3: "vuelo_fotografico",
    4: "aeromodelismo",
    6: "zona_aerodromo",
    10: "zona_restringida"
}

# Subtypes para FeatureServer
SUBTYPE_CAPA_FEATURE = {
    0: "infraestructura",
    2: "zona_aero",
    3: "zona_urbana"
}

# Colores para cada tipo de zona
COLORES = {
    0: "#ffaa00",      # Naranja - Aeródromos
    1: "#3b82f6",      # Azul - Espacio controlado (FIZ)
    2: "#f97316",      # Naranja oscuro - NOTAM
    3: "#eab308",     # Amarillo - Vuelo fotográfico restringido
    4: "#a855f7",     # Púrpura - Aeromodelismo
    6: "#22c55e",     # Verde - ZG Aeródromos
    10: "#ef4444"     # Rojo - Zonas restringidas
}

# Colores para FeatureServer
COLORES_FEATURE = {
    0: "#6b7280",     # Gris - Infraestruturas
    2: "#ffaa00",     # Naranja - ZG Aero
    3: "#f43f5e"     # Rosa - Zonas urbanas
}


def convertir_3857_a_4326(x, y):
    """Convierte coordenadas EPSG:3857 (Web Mercator) a EPSG:4326 (lat/lon)"""
    lon = (x / 20037508.34) * 180
    lat = (y / 20037508.34) * 180
    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return lat, lon


def es_wgs84(x, y):
    """Detecta si las coordenadas ya están en WGS84 (sin conversión necesaria)"""
    # Si x e y están en rangos válidos de lat/lon, ya están en WGS84
    return -180 <= float(x) <= 180 and -90 <= float(y) <= 90


def convertir_anillo_a_coords(ring):
    """Convierte un anillo de polígono a coordenadas EPSG:4326 (lat/lon)"""
    coords = []
    skipped = 0

    # Verificar el primer punto para determinar el formato
    if ring and len(ring) > 0 and isinstance(ring[0], (list, tuple)) and len(ring[0]) >= 2:
        primer_punto = ring[0]
        x, y = float(primer_punto[0]), float(primer_punto[1])

        # Si ya está en WGS84, no convertir
        if es_wgs84(x, y):
            # Ya está en formato [lon, lat] - convertir a [lat, lon]
            for point in ring:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    lon, lat = float(point[0]), float(point[1])
                    coords.append([lat, lon])
                else:
                    skipped += 1
        else:
            # Está en EPSG:3857 - convertir a EPSG:4326
            for point in ring:
                if isinstance(point, (list, tuple)) and len(point) >= 2:
                    try:
                        lat, lon = convertir_3857_a_4326(float(point[0]), float(point[1]))
                        coords.append([lat, lon])
                    except (ValueError, TypeError) as e:
                        continue
                else:
                    skipped += 1

    # Cerrar el polígono si no lo está
    if coords and coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def convertir_geom_a_geojson(geom):
    """Convierte geometría del MapServer de ENAIRE a formato GeoJSON"""
    if not geom:
        return None

    if "x" in geom and "y" in geom:
        # Es un punto - detectar formato
        x, y = float(geom["x"]), float(geom["y"])
        try:
            if es_wgs84(x, y):
                # Ya está en WGS84 - formato [lon, lat]
                return {"type": "Point", "coordinates": [x, y]}
            else:
                # Está en EPSG:3857 - convertir
                lat, lon = convertir_3857_a_4326(x, y)
                return {"type": "Point", "coordinates": [lon, lat]}
        except (ValueError, TypeError, KeyError) as e:
            print(f"[DRONES] Error convirtiendo punto: {e}")
            return None
    elif "rings" in geom:
        # Es un polígono
        rings = []
        try:
            for ring in geom["rings"]:
                converted_ring = convertir_anillo_a_coords(ring)
                if converted_ring:
                    rings.append(converted_ring)

            if len(rings) == 1:
                # Crear resultado completamente nuevo - con anidación correcta para GeoJSON
                new_coords = []
                for c in rings[0]:
                    new_coords.append([float(c[0]), float(c[1])])
                # GeoJSON Polygon requiere: coordinates = [ring] donde ring = [[lon,lat], ...]
                return {"type": "Polygon", "coordinates": [new_coords]}
            elif len(rings) > 1:
                return {"type": "MultiPolygon", "coordinates": rings}
        except Exception as e:
            print(f"[DRONES] Error convirtiendo anillos: {e}")
            return None
    return None


class DronesLayer:
    def __init__(self):
        self.id = "drones"
        self.enabled = True

    def _procesar_feature(self, feature, nombre_capa, id_capa, es_feature_server=False):
        """Procesa un feature y devuelve una zona"""
        try:
            attrs = feature.get("attributes", {})
            geom = feature.get("geometry", {})

            # Extraer nombre/identificador
            nombre = (attrs.get("IDENT_TXT") or
                     attrs.get("NOMBRE") or
                     attrs.get("NAME") or
                     attrs.get("NOMBRE_TXT") or
                     f"{nombre_capa}_{attrs.get('OBJECTID', attrs.get('FID', ''))}")

            # Convertir geometría a GeoJSON
            geojson_geom = convertir_geom_a_geojson(geom)
            if not geojson_geom:
                return None

            # Extraer información relevante (solo tipos serializables)
            info = {}
            excluded_keys = ['OBJECTID', 'SHAPE', 'SHAPE_LENGTH', 'SHAPE_AREA',
                           'SHAPE.STArea()', 'SHAPE.STLength()', 'FID']
            for key in attrs.keys():
                if key in excluded_keys:
                    continue
                val = attrs[key]
                # Solo incluir valores que sean serializables JSON
                if isinstance(val, (str, int, float, bool, type(None))):
                    info[key] = val
                elif isinstance(val, list):
                    try:
                        import json
                        json.dumps(val)
                        info[key] = val
                    except:
                        info[key] = str(val)[:500]
                else:
                    info[key] = str(val)[:500]

            # Seleccionar mapeos según el servidor
            nombre_map = NOMBRE_CAPA_FEATURE if es_feature_server else NOMBRE_CAPA
            subtype_map = SUBTYPE_CAPA_FEATURE if es_feature_server else SUBTYPE_CAPA
            colores_map = COLORES_FEATURE if es_feature_server else COLORES

            zona = {
                "source": self.id,
                "type": "zone",
                "subtype": subtype_map.get(id_capa, "zona_drone"),
                "name": nombre,
                "geometry": geojson_geom,
                "capa": nombre_map.get(id_capa, nombre_capa),
                "color": colores_map.get(id_capa, "#ffffff"),
                "info": info
            }

            # Si es un punto, añadir lat/lon
            if geojson_geom.get("type") == "Point":
                zona["lat"] = geojson_geom["coordinates"][1]
                zona["lon"] = geojson_geom["coordinates"][0]
            # Si es polígono, calcular centroide
            elif geojson_geom.get("type") == "Polygon":
                try:
                    coords = geojson_geom.get("coordinates", [[]])[0]
                    if coords and isinstance(coords, list) and len(coords) > 0:
                        lons = [c[0] for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
                        lats = [c[1] for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
                        if lons and lats:
                            zona["lat"] = sum(lats) / len(lats)
                            zona["lon"] = sum(lons) / len(lons)
                except Exception as e:
                    print(f"[DRONES] Error calculando centroide polígono: {e}")
            elif geojson_geom.get("type") == "MultiPolygon":
                try:
                    coords = geojson_geom.get("coordinates", [[]])[0][0]
                    if coords and isinstance(coords, list) and len(coords) > 0:
                        lons = [c[0] for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
                        lats = [c[1] for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
                        if lons and lats:
                            zona["lat"] = sum(lats) / len(lats)
                            zona["lon"] = sum(lons) / len(lons)
                except Exception as e:
                    print(f"[DRONES] Error calculando centroide multipolygon: {e}")

            return zona
        except Exception as inner_e:
            import traceback
            print(f"[DRONES] Error procesando feature en {nombre_capa}: {inner_e}")
            traceback.print_exc()
            return None

    def fetch(self):
        """Obtiene zonas de vuelo de drones de la API de ENAIRE (todas las capas)"""
        zonas = []
        try:
            # === CONSULTAR MAPSERVER (capas principales) ===
            for nombre_capa, id_capa in CAPAS_MAP.items():
                url = f"{ENAIRE_MAP_SERVER}/{id_capa}/query"
                params = {
                    "where": "1=1",
                    "outFields": "*",
                    "resultRecordCount": 500,
                    "f": "json",
                    "returnGeometry": "true"
                }
                try:
                    res = requests.get(url, params=params, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        features = data.get("features", [])
                        print(f"[DRONES] {nombre_capa}: {len(features)} features obtenidos")
                        for feature in features:
                            zona = self._procesar_feature(feature, nombre_capa, id_capa, False)
                            if zona:
                                zonas.append(zona)
                except Exception as e:
                    print(f"[DRONES] Error consultando {nombre_capa} (ID {id_capa}): {e}")
                    continue

            # === CONSULTAR FEATURESERVER (capas adicionales) ===
            for nombre_capa, id_capa in CAPAS_FEATURE.items():
                url = f"{ENAIRE_FEATURE_SERVER}/{id_capa}/query"
                params = {
                    "where": "1=1",
                    "outFields": "*",
                    "resultRecordCount": 500,
                    "f": "json",
                    "returnGeometry": "true"
                }
                try:
                    res = requests.get(url, params=params, timeout=15)
                    if res.status_code == 200:
                        data = res.json()
                        features = data.get("features", [])
                        print(f"[DRONES] {nombre_capa}: {len(features)} features obtenidos")
                        for feature in features:
                            zona = self._procesar_feature(feature, nombre_capa, id_capa, True)
                            if zona:
                                zonas.append(zona)
                except Exception as e:
                    print(f"[DRONES] Error consultando {nombre_capa} (ID {id_capa}): {e}")
                    continue

            # Limitar el número total de zonas (aumentado para mostrar todas las capas)
            out = zonas[:2000]
            mark_fresh(self.id)
            print(f"[DRONES] Zonas obtenidas: {len(out)}")
            return out

        except Exception as e:
            print(f"[DRONES] Error general: {e}")
            mark_fresh(self.id)
            return []