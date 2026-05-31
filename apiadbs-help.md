# adsbdb - API de Aviones y Rutas de Vuelo

## Resumen

**adsbdb** es una API pública para obtener información detallada sobre aviones comerciales, airlines y flight routes. Está construida en Rust con axum, usando PostgreSQL y Redis.

Enlace: https://github.com/mrjackwills/adsbdb

## Características Principales

- Datos de aviones por MODE-S hex o registration
- Información de aerolineas (ICAO/IATA)
- Rutas de vuelo (origen/destino)
- Conversión MODE-S ↔ N-Number
- Fotos de aviones (thumbnails)
- Sin autenticación requerida (acceso público)

## Endpoints Disponibles

| Endpoint | Descripción |
|----------|-------------|
| `/v0/aircraft/[MODE_S]` | Datos del avión por MODE-S hex |
| `/v0/aircraft/[REGISTRATION]` | Datos del avión por matrícula |
| `/v0/aircraft/random` | Avión aleatorio |
| `/v0/callsign/[CALLSIGN]` | Info de ruta por callsign |
| `/v0/callsign/random` | Ruta aleatoria |
| `/v0/airline/[ICAO]` | Info de aerolinea por código ICAO |
| `/v0/airline/[IATA]` | Info de aerolinea por código IATA |
| `/v0/stats` | Estadísticas de uso de la API |
| `/v0/mode-s/[MODE_S]` | Convierte MODE-S a N-Number |
| `/v0/n-number/[N-NUMBER]` | Convierte N-Number a MODE-S |

## Datos que Devuelve

### Avión
```json
{
  "icao24": "4cadbc",
  "registration": "EC-LZX",
  "type": "Boeing 737-8K2",
  "icaoType": "B738",
  "manufacturer": "Boeing",
  "operatorFlagCode": "IBE",
  "operatorName": "Iberia",
  "ownerName": "Air Lease Corporation",
  "country": "Spain",
  "photoUrl": "https://...",
  "photoUrlThumbnail": "https://..."
}
```

### Ruta de Vuelo
```json
{
  "callsign": "IBE1234",
  "airline": {
    "name": "Iberia",
    "icao": "IBE",
    "iata": "IB",
    "country": "Spain"
  },
  "origin": {
    "icao": "LEMD",
    "iata": "MAD",
    "name": "Adolfo Suárez Madrid-Barajas Airport",
    "lat": 40.4983,
    "lon": -3.5676
  },
  "destination": {
    "icao": "LEBL",
    "iata": "BCN",
    "name": "Barcelona-El Prat Airport",
    "lat": 41.2974,
    "lon": 2.0833
  }
}
```

## Ejemplo de Uso en Ojo Backend

### 1. Agregar como nueva capa

Crear `layers/adsbdb/layer.py`:

```python
import requests
from typing import List, Dict, Any
from core.store import mark_fresh

ADSBCDB_API = "https://api.adsbdb.com/v0"

class ADSBDbLayer:
    def __init__(self):
        self.id = "adsbdb"
        self.enabled = True
        self.cache = {}

    def fetch(self) -> List[Dict[str, Any]]:
        """Nofetch - esta capa sirve para enriquecer datos, no como fuente primaria"""
        return []

    def get_aircraft_details(self, icao24: str) -> Dict[str, Any]:
        """Obtiene detalles de un avión por su MODE-S"""
        url = f"{ADSBCDB_API}/aircraft/{icao24}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json().get("data", {})
        except Exception:
            pass
        return {}

    def get_route_by_callsign(self, callsign: str) -> Dict[str, Any]:
        """Obtiene ruta de vuelo por callsign"""
        url = f"{ADSBCDB_API}/callsign/{callsign}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json().get("data", {})
        except Exception:
            pass
        return {}
```

### 2. Enriquecer datos de ADS-B

En el backend, después de obtener los datos de la capa adsb:

```python
# En api/main.py o en el layer_engine
from layers.adsbdb.layer import ADSBDbLayer

adsbdb = ADSBDbLayer()

# Enriquecer cada avión con datos adicionales
for aircraft in adsb_data:
    icao24 = aircraft.get("id")  # MODE-S hex
    details = adsbdb.get_aircraft_details(icao24)

    # Agregar datos enrichidos al avión
    aircraft["registration"] = details.get("registration")
    aircraft["aircraft_type"] = details.get("type")
    aircraft["manufacturer"] = details.get("manufacturer")
    aircraft["operator"] = details.get("operatorName")
    aircraft["owner"] = details.get("ownerName")
    aircraft["country"] = details.get("country")
    aircraft["photo_url"] = details.get("photoUrl")
    aircraft["photo_thumbnail"] = details.get("photoUrlThumbnail")
```

### 3. Obtener ruta de vuelo por callsign

```python
# Cuando el usuario hace clic en un avión, mostrar ruta
callsign = aircraft.get("name")
route = adsbdb.get_route_by_callsign(callsign)

if route:
    print(f"Ruta: {route['origin']['iata']} → {route['destination']['iata']}")
    print(f"Aerolínea: {route['airline']['name']}")
```

## Integración Directa con el Frontend

También puedes hacer llamadas directas desde el frontend para enriquecer datos:

```javascript
// En el popup del avión, al hacer clic
async function enrichAircraft(icao24) {
  const response = await fetch(`https://api.adsbdb.com/v0/aircraft/${icao24}`);
  const data = await response.json();
  return data.data;
}

// Uso
const details = await enrichAircraft(aircraftId);
// Mostrar foto, matrícula, operador, etc.
```

## Despliegue Local (Opcional)

Si quieres tu propia instancia de adsbdb:

```bash
# Con Docker
git clone https://github.com/mrjackwills/adsbdb.git
cd adsbdb
./run.sh

# La API estará en http://localhost:8080
```

## Límites y Consideraciones

- **Sin auth**: La API pública no requiere autenticación
- **Rate limit**: Puede tener límites - usar con moderación
- **Cache**: Implementar cache local para evitar llamadas repetidas
- **Datos**: Usa PlaneBase como fuente principal de datos de aviones

## En Resumen

adsbdb permite enriquecer los datos de aviones de tu proyecto con:

1. **Matrícula** (registration) - Ej: EC-LZX
2. **Tipo de aeronave** - Ej: Boeing 737-8K2
3. **Fabricante** - Ej: Boeing
4. **Operador** - Ej: Iberia
5. **Propietario** - Ej: Air Lease Corporation
6. **País de registro** - Ej: Spain
7. **Fotos** - URLs de imágenes del avión
8. **Rutas de vuelo** - Origen/destino por callsign

Es un complemento ideal para las capas `adsb` y `enaire` que ya tienes en tu proyecto.