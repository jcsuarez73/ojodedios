# Resumen: Problema de datos en ojo_backend

## Estado de la investigación

### API devuelve datos correctamente
La API en `http://localhost:8095/layers` retorna:
- downdetector (simulado)
- airnavradar
- ourairports
- geamap
- thousandeyes
- races
- aisstream
- drones

### Capas sin datos
- **n2yo**: Usa API key "DEMO_KEY" - necesita clave real
- **enaire**: No retorna datos (last_updated: null)

### Frontend
El frontend en `static/index.html` hace polling a:
- `/layers` cada 2 segundos
- `/layers/sources` cada 10 segundos

## Pendiente
- Revisar por qué los datos no se renderizan en el mapa
- Posible problema en el JavaScript del frontend