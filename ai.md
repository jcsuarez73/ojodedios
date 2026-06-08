---
name: Ojo Backend - Sistema de Agregación de Datos
description: Backend FastAPI para agregar datos de múltiples fuentes (satélites,aviones,barcos,drones,aeropuertos)
type: user
---

# Proyecto: Ojo Backend

## Resumen

API backend construida con **FastAPI** que agrega datos de múltiples fuentes/capas en tiempo real. El sistema está diseñado como un agregador de datos geoespaciales de fuentes públicas y privadas.

## Stack Tecnológico

- **Framework**: FastAPI + Uvicorn
- **Puerto**: 8095
- **Python**: 3.11
- **Contenedor**: Docker
- **APIs externas**: N2YO, OpenSky, Celestrak, AISStream, Enaire, adsb.lol, ENAIRE Drones

## Estructura del Proyecto

```
ojo_backend/
├── api/
│   └── main.py           # Punto de entrada FastAPI
├── core/
│   ├── models.py         # Modelos de datos (normalize_point)
│   ├── registry.py       # Registro de capas disponibles
│   ├── store.py          # Almacén de estado
│   └── layer_engine.py  # Motor de ejecución de capas
├── layers/               # Módulos de fuentes de datos
│   ├── n2yo/             # Satélites (N2YO API)
│   ├── celestrak/        # Satélites (Celestrak)
│   ├── enaire/           # Tráfico aéreo español
│   ├── adsb/             # Datos ADSB
│   ├── airnavradar/      # Radar aéreo
│   ├── ourairports/      # Aeropuertos
│   ├── geamap/           # Mapa Gea
│   ├── thousandeyes/    # Thousand Eyes
│   ├── races/           # Carreras
│   ├── aisstream/       # Barcos (AIS)
│   ├── drones/          # Drones
│   └── downdetector/    # Estado de servicios
├── static/
│   └── index.html       # Frontend estático
├── config/              # Directorio de configuración
├── Dockerfile          # Imagen Docker
├── docker-compose.yml   # Orquestación
├── requirements.txt    # Dependencias Python
└── HELP.md            # Documentación de ayuda
```

## Capas Disponibles (12 layers)

| Capa | Descripción |
|------|-------------|
| n2yo | Satélites artificiales (API N2YO) |
| celestrak | Satélites (Celestrak TLE) |
| enaire | Tráfico aéreo español |
| adsb | Datos ADSB (aviones) |
| airnavradar | Radar AirNav |
| ourairports | Aeropuertos mundiales |
| geamap | Mapa Gea |
| thousandeyes | Network monitoring |
| races | Carreras/Eventos |
| aisstream | Barcos (AIS marine traffic) |
| drones | Zonas de vuelo de drones (ENAIRE) - Polígonos GeoJSON |
| downdetector | Estado de servicios |

## Endpoints API

- `GET /layers` - Datos de todas las capas con metadatos
- `GET /layers/data` - Solo datos crudos (legacy)
- `GET /layers/sources` - Información de fuentes
- `GET /layers/status` - Estado de capas (enabled/disabled)
- `GET /layer/{name}/toggle` - Alternar capa on/off
- `WS /ws` - WebSocket de debug

## API Principal

```python
# Entry point: api/main.py
from core.registry import LayerRegistry
from core.layer_engine import LayerEngine

registry = LayerRegistry()  # Carga las 12 capas
engine = LayerEngine(registry)
```

## Modelos de Datos

```python
# core/models.py
def normalize_point(source, subtype, lat=None, lon=None, metadata=None):
    return {
        "source": source,
        "type": "asset",
        "subtype": subtype,
        "lat": lat,
        "lon": lon,
        "metadata": metadata or {}
    }
```

## Variables de Entorno

- `N2YO_API_KEY` - Clave API N2YO
- `OPENSKY_USERNAME` - Usuario OpenSky
- `OPENSKY_PASSWORD` - Contraseña OpenSky

## Ejecución

```bash
# Local con Docker
docker-compose up

# Desarrollo directo
uvicorn api.main:app --host 0.0.0.0 --port 8095 --reload
```

## Características Principales

1. **Sistema de plugins (layers)**: Cada fuente de datos es una capa independiente
2. **Registro dinámico**: Las capas se cargan desde `core/registry.py`
3. **Estado persistente**: `core/store.py` guarda el estado de capas activas
4. **WebSocket**: Endpoint de debug para conexiones en tiempo real
5. **CORS habilitado**: Permite acceso cruzado para desarrollo local
6. **Static files**: Serve HTML desde `static/`

## Cómo Agregar una Nueva Capa

1. Crear carpeta en `layers/nueva_capa/`
2. Crear `layer.py` con clase que herede de base
3. Importar y registrar en `core/registry.py`
4. La capa debe tener `id` y `enabled`

## Capa Drones (Zonas ENAIRE) - Análisis comparativo

La aplicación ENAIRE Drones (drones.enaire.es) usa:
- Mapa base: ArcGIS
- Tipos de zonas: Polígonos, puntos, círculos, líneas
- Sistema de simbología NOTAM v2.2
- Colores: Naranja para UI, simbología específica por tipo de zona

### Nuestra implementación actual

La capa `drones` obtiene zonas de vuelo de drones de la API de ENAIRE. Se consultan **dos servidores**:

### MapServer (capas principales)
- **URL**: `https://servais.enaire.es/insignias/rest/services/NSF/Drones_ZG_Aero_V0/MapServer`
- **Capas disponibles**:
  - ID 0: Aeródromos
  - ID 1: ZG_EAC_FIZ (Espacio Controlado)
  - ID 2: NOTAM (Avisos)
  - ID 3: ZG_RVF (Restringido Vuelo Fotográfico)
  - ID 4: Aeromodelismo
  - ID 6: ZG_Aeródromos
  - ID 10: ZG_Restringidas

### FeatureServer (capas adicionales)
- **URL**: `https://servais.enaire.es/insignia/rest/services/NSF_SRV/SRV_UAS_ZG_V1/FeatureServer`
- **Capas disponibles**:
  - ID 0: ZG_Infraestructuras
  - ID 2: ZG_Aero
  - ID 3: ZG_Urbano

### Capas totales disponibles (10):
1. Aeromodelismo
2. Aerodromos
3. NOTAM
4. ZG_aerodromos
5. ZG_EAC_FIZ
6. ZG_Restringidas
7. ZG_RVF (restringido vuelo fotográfico)
8. ZG_Infraestructuras
9. ZG_Urbano

### Métricas de Zonas (2026-06-06)
- **Total zonas cargadas**: ~2000 (límite del sistema)
- **ZG_EAC_FIZ**: 101 zonas (Espacio Controlado)
- **ZG_RVF**: 119 zonas
- **ZG_Restringidas**: 108 zonas
- **NOTAM**: 184 zonas

### Corrección aplicada (2026-06-06)

**Problema**: Las zonas de drones (polígonos) se renderizaban con solo 2 coordenadas en lugar de las 186+ originales.

**Causa raíz**: La función `convertir_geom_a_geojson` creaba una estructura GeoJSON incorrecta. El estándar GeoJSON para Polygon requiere:
```json
{"type": "Polygon", "coordinates": [ring]}  // ring = [[lon,lat], ...]
```
Pero el código generaba:
```json
{"type": "Polygon", "coordinates": [[lon,lat], ...]}  // Sin el array de anillos
```

**Solución**: En `layers/drones/layer.py`, cambiar la línea de retorno de:
```python
return {"type": "Polygon", "coordinates": new_coords}
```
a:
```python
return {"type": "Polygon", "coordinates": [new_coords]}
```

**Archivo**: `layers/drones/layer.py`, función `convertir_geom_a_geojson()`, línea ~185

### Formato de salida

```json
{
  "source": "drones",
  "type": "zone",
  "subtype": "zona_aerodromo",
  "name": "LEBL",
  "geometry": {"type": "Polygon", "coordinates": [...]},
  "color": "#ffaa00",
  "info": {
    "lower": 45,
    "upper": 900,
    "lowerReference": "AGL",
    "type": "REQ_AUTHORIZATION"
  }
}
```

## Colores por Altitud (Aviones)

Las capas `adsb` y `enaire` incluyen colores según la altitud del avión:

| Altitud | Color | Hue |
|---------|-------|-----|
| < 500 ft | 🔴 Rojo | 1 |
| 500 ft | 🟠 Naranja | 30 |
| 2,000 ft | 🟡 Amarillo | 60 |
| 5,000 ft | 🟢 Verde | 120 |
| 10,000 ft | 🔵 Cian | 180 |
| 20,000 ft | 🔵 Azul | 240 |
| 40,000 ft | 🔴 Magenta | 300 |
| 60,000+ ft | 🔴 Rojo | 360 |

## Cambios Recientes (2026-06-08)

### Opacidad Zonas ENAIRE
- Las zonas de restricciones de drones/ENaire ahora tienen **80% de opacidad** (antes 55%)
- Archivo: `static/index.html`, línea ~1451

### Botón MAP (DARK/RELIEVE)
- Toggle para cambiar mapa base entre CartoDB Dark y relieve topográfico
- Ubicación: Debajo del botón LAYERS
- Relieve usa OpenStreetMap US Hillshade (gratuito)
- Implementado con 6 consultas paralelas y dedup por hex ICAO

### Cobertura Global ADSB.lol
- La API de adsb.lol limita consultas a ~2500nm por punto
- NO existe endpoint global - solo consultas por radio
- Solución implementada: 6 consultas en paralelo a diferentes puntos del mundo:
  1. Europa central (lat: 48, lon: 10, radius: 2500)
  2. Atlántico norte (lat: 45, lon: -30, radius: 2500)
  3. USA centro (lat: 40, lon: -100, radius: 2500)
  4. Latinoamérica (lat: -15, lon: -60, radius: 2500)
  5. USA East Coast / Caribe (lat: 30, lon: -80, radius: 2500)
  6. Japón / Asia Este (lat: 35, lon: 140, radius: 2500)
- Deduplicación por hex ICAO para evitar duplicados
- Archivo: `layers/adsb/layer.py`