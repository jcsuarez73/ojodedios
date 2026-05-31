# OJO DE DIOS - Global Operations Aircraft Tracking

> *"Hecho con amor y dedicación mientras mi Padre, El Rey del Tubey, pasaba sus últimas días convaleciente y enfermo hasta su muerte el 13-05-2026 en Venezuela. Este proyecto me mantuvo la mente tranquila y ocupada durante esos momentos difíciles."*

---
<img width="1440" height="796" alt="image" src="https://github.com/user-attachments/assets/27565f94-f5d2-4026-a040-2391064abc53" />



## Descripción

**OJO DE DIOS** es un sistema de monitoreo en tiempo real de Aeronaves, Barcos, Satélites y otras fuentes de datos mediante un mapa interactivo. El proyecto visualiza posiciones de aeronaves ADS-B, datos de ENAIRE (espacio aéreo español), notificaciones NOTAM, y otras fuentes de inteligencia operacional.

### Características Principales

- 🛩️ **Monitoreo de aeronaves** en tiempo real (España y cercanías)
- 🛰️ **Seguimiento de satélites** en órbita
- 🚢 **Tráfico marítimo** (AIS)
- 🚁 **Zonas de vuelo de drones** (ENAIRE)
- ⚠️ **Espacios aéreo restringidos** y controladas
- 📡 **Múltiples fuentes de datos** integradas

---

## Tecnologías Usadas

### Backend
- **Python 3.14+** - Lenguaje principal
- **FastAPI** - Framework web y API REST
- **Uvicorn** - Servidor ASGI

### Frontend
- **HTML5/CSS3** - Interfaz visual
- **JavaScript** - Lógica del cliente
- **Leaflet.js** - Biblioteca de mapas interactivos
- **CartoDB Dark Matter** - Mapas base oscuro

### Arquitectura
- Sistema de **capas modulares** - Cada fuente de datos es una capa independiente
- API REST para consulta de datos en tiempo real
- Actualización automática cada 2 segundos

---

## Instalación y Uso

### Requisitos Previos
- Python 3.14+
- Git

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/jcsuarez73/ojodedios.git
cd ojodedios

# Crear entorno virtual (opcional)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecución

```bash
# Iniciar el servidor
python -m uvicorn core.app:app --host 0.0.0.0 --port 8095 --reload
```

### Acceso

Abre tu navegador en: `http://localhost:8095`

---

## Fuentes de Datos

| Fuente           | Descripción                        | Tipo de Datos           |
|------------------|------------------------------------|-------------------------|
| **ADSB.lol**     | API pública de rastreo aeronautico | Aeronaves               |
| **ENAIRE**       | Espacio aéreo español              | Aeronaves, zonas drones |
| **N2YO**         | Satélites en tiempo real           | Satélites orbitales     |
| **Celestrak**    | Base de datos de satélites         | Catálogo orbital        |
| **OurAirports**  | Aeropuertos mundial                | Aeródromos              |
| **AISStream**    | Tráfico marítimo                   | Barcos                  |
| **GeaMap**       | Datos geográficos                  | Puntos de interés       |
| **ThousandEyes** | Monitor de red                     | Estado de red           |
| **DownDetector** | Estado de servicios                | Incidencias             |

---

## Gamma de Colores - Altitud de Aeronaves

Los colores de las aeronaves y la barra de altitud siguen el esquema de **ADS-B.lol**:
|-----------------|--------------------|---------------------|
| Altitud (pies)  | Color              | Descripción         |
|-----------------|--------------------|---------------------|
| < 500           | 🔴 Rojo            | Muy baja altitud    |
| 500 - 1,000     | 🟠 Naranja         | Baja altitud        |
| 1,000 - 2,000   | 🟡 Amarillo        | Ascension/Descenso  |
| 2,000 - 5,000   | 🟢 Verde           | Tráfico regional    |
| 5,000 - 10,000  | 🔵 Cian            | Tráfico nacional    |
| 10,000 - 20,000 | 🔵 Azul            | Alta altitud        |
| 20,000 - 40,000 | 🟣 Púrpura/Magenta | Muy alta altitud    |
| > 40,000        | 🔴 Rojo (ciclo)    | Extremadamente alta |
|-----------------|--------------------|---------------------|
### Fórmula de Colores

```python
# Puntos de control (altitud en pies, hue)
points = [
    (500, 1),      # rojo
    (1000, 30),    # naranja
    (2000, 60),    # amarillo
    (5000, 120),   # verde
    (10000, 180),  # cian
    (20000, 240),  # azul
    (40000, 300),  # magenta
    (60000, 360),  # rojo (ciclo completo)
]
```

---

## Capas de Zonas de Drones (ENAIRE)

Las zonas de vuelo de drones se muestran como **polígonos** con los siguientes colores:

| Tipo de Zona | Color |
|--------------|-------|
| Aeródromos   | 🟠 Naranja |
| Aeromodelismo | 🟣 Púrpura |
| Zonas Aeródromos | 🟢 Verde |
| Espacio Controlado (EAC/FIZ) | 🔵 Azul |
| **Zonas Restringidas** | 🔴 Rojo |
| Vuelo Fotográfico | 🟡 Amarillo |
| Avisos | 🟠 Naranja |

---

## Estructura del Proyecto

```
ojodedios/
├── core/
│   ├── app.py          # Aplicación FastAPI
│   ├── store.py        # Almacén de datos
│   └── models.py       # Modelos de datos
├── layers/             # Módulos de capas de datos
│   ├── adsb/           # Datos ADS-B
│   ├── enaire/         # Espacio aéreo ENAIRE
│   ├── drones/         # Zonas de drones
│   ├── n2yo/           # Satélites N2YO
│   └── ...
├── static/
│   └── index.html      # Frontend del mapa
├── config/             # Configuración
├── requirements.txt   # Dependencias Python
└── README.md          # Este archivo
```

---

## API Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `/layers` | Obtiene todos los datos de capas activas |
| `/layers/sources` | Estado de las fuentes de datos |
| `/layer/{name}/toggle` | Activa/desactiva una capa |

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o Pull Request.

---

## Licencia

MIT License - Libre uso y modificación.

---

## Dedicatoria

> *"Este proyecto fue creado durante los momentos más difíciles de mi vida, mientras mi padre enfrentaba su enfermedad terminal en Venezuela. Trabajar en esto me ayudó a mantener mi mente ocupada y en calma. Para ti, Papá. Tu memoria vive en cada línea de código."*

**Juan Carlos Suárez** - Mayo 2026

---

*Global Operations Aircraft Tracking - OJO DE DIOS*
