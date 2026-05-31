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
- **APIs externas**: N2YO, OpenSky, Celestrak, AISStream, Enaire

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
| drones | Drones |
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