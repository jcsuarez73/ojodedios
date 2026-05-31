import sys
import os
import asyncio
import random
from fastapi import FastAPI, WebSocket
from core.registry import LayerRegistry
from core.layer_engine import LayerEngine
from core.store import active_layers, get_all_sources_info
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ==============================================================================
# 1. SEGURIDAD DE RED (CORS) - Siempre arriba
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite accesos cruzados sin restricciones en tu entorno local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización legítima del registro y motor táctico de Shadowbroker
registry = LayerRegistry()
engine = LayerEngine(registry)

# ==============================================================================
# 2. RUTAS HTTP DE LA API
# ==============================================================================

@app.get("/layers")
def layers():
    """Get all layer data with source metadata."""
    return engine.collect_with_metadata()

@app.get("/layers/data")
def layers_data():
    """Get only the raw data from layers (legacy endpoint)."""
    return engine.collect()

@app.get("/layers/sources")
def layers_sources():
    """Get source information for all layers."""
    return get_all_sources_info()

@app.get("/layers/status")
def layers_status():
    """Get the status of all layers (enabled/disabled)."""
    return {
        "active_layers": active_layers,
        "sources": get_all_sources_info()
    }

@app.get("/layer/{name}/toggle")
def toggle_layer(name: str):
    print(f"📡 Petición de alternancia recibida para la capa: {name}")

    try:
        # Ejecuta la lógica nativa de tu core para activar/desactivar la capa
        registry.toggle(name)
    except Exception as e:
        print(f"⚠️ Error al alternar la capa [{name}] en el core: {e}")

    # Intentamos extraer el estado real si tu capa expone 'enabled' o similar
    is_enabled = True
    if hasattr(registry, 'layers') and name in registry.layers:
        layer_obj = registry.layers[name]
        is_enabled = getattr(layer_obj, 'enabled', True)

    return {
        "layer": name,
        "enabled": is_enabled
    }

# ==============================================================================
# 3. WEBSOCKET - MÓDULO DE DEPURACIÓN PASIVO
# ==============================================================================
@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    print("🔌 [DEBUG] ¡TUBERÍA ABIERTA TOTALMENTE!")

    # Datos mínimos directos de control
    TEST_DATA = [
        {"source": "n2yo", "id": "SAT-FIXED", "lat": 40.4167, "lon": -3.7037}
    ]

    try:
        await websocket.send_json({
            "type": "layers_update",
            "data": TEST_DATA
        })
        print("📡 [DEBUG] Primer paquete enviado con éxito.")

        while True:
            # Mantiene la conexión viva esperando datos sin interferir con el bucle HTTP
            await websocket.receive_text()
    except Exception as e:
        print(f"🔌 [DEBUG] Conexión cerrada: {e}")

# ==============================================================================
# 4. MONTADO ESTÁTICO (SIEMPRE AL FINAL)
# ==============================================================================
app.mount("/", StaticFiles(directory="static", html=True), name="static")