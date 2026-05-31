from core.store import get_all_sources_info, source_timestamps, mark_fresh
from datetime import datetime

class LayerEngine:
    def __init__(self, registry):
        self.registry = registry
        self.last_state = []   # 🔥 BUFFER AQUÍ
        self.last_sources = {}  # Store source info

    def collect(self):
        data = []

        for layer in self.registry.get_layers():
            try:
                data.extend(layer.fetch())
                # La capa ya llama a mark_fresh internamente si tiene datos
            except Exception as e:
                print(f"[ERROR LAYER] {layer.id}: {e}")
                # También marcamos como fresh aunque haya fallado
                mark_fresh(layer.id)

        # 🔥 GUARDAMOS ESTADO (BUFFER)
        self.last_state = data

        # Guardar info de fuentes
        self.last_sources = get_all_sources_info()

        return data

    def collect_with_metadata(self):
        """Collect data along with source metadata."""
        data = self.collect()

        return {
            "data": data,
            "sources": self.last_sources,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_sources(self):
        """Get source information without fetching new data."""
        return get_all_sources_info()

    def get_last_state(self):
        return self.last_state