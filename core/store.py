"""Shared in-memory data store for layer sources.

Central location for active_layers and source_timestamps.
"""
from datetime import datetime
from typing import Dict, Any

# Active layers — frontend toggles these, fetchers check before running
active_layers: Dict[str, bool] = {
    "n2yo": True,
    "celestrak": True,
    "enaire": True,
    "adsb": True,
    "downdetector": True,
    "airnavradar": True,
    "ourairports": True,
    "geamap": True,
    "thousandeyes": True,
    "races": True,
    "aisstream": True,
    "drones": True,
}

# Per-source freshness timestamps
source_timestamps: Dict[str, str] = {}

# Source metadata - maps layer_id to source name and type
source_metadata: Dict[str, Dict[str, str]] = {
    "n2yo": {
        "source": "N2YO API",
        "source_type": "satellite_tle",
        "description": "Satellite position data from N2YO"
    },
    "celestrak": {
        "source": "Celestrak",
        "source_type": "satellite_tle",
        "description": "Satellite TLE data from Celestrak (free)"
    },
    "enaire": {
        "source": "OpenSky Network",
        "source_type": "adsb",
        "description": "Aircraft positions from Enaire/OpenSky"
    },
    "adsb": {
        "source": "ADSB.lol",
        "source_type": "adsb",
        "description": "Live aircraft tracking from ADSB.lol"
    },
    "downdetector": {
        "source": "DownDetector (simulado)",
        "source_type": "outage",
        "description": "Service outage reports"
    },
    "airnavradar": {
        "source": "AirNav Radar",
        "source_type": "radar",
        "description": "Air navigation radar stations"
    },
    "ourairports": {
        "source": "OurAirports",
        "source_type": "airports",
        "description": "Airport locations and information"
    },
    "geamap": {
        "source": "GeaMap",
        "source_type": "geological",
        "description": "Geological points and volcanic data"
    },
    "thousandeyes": {
        "source": "ThousandEyes",
        "source_type": "network",
        "description": "Network test points and monitoring"
    },
    "races": {
        "source": "Races.es",
        "source_type": "events",
        "description": "Race tracks and motorsport events"
    },
    "aisstream": {
        "source": "AISStream",
        "source_type": "maritime",
        "description": "Maritime vessel tracking"
    },
    "drones": {
        "source": "Drones ENAIRE",
        "source_type": "drone_zones",
        "description": "Drone restriction zones"
    }
}


def mark_fresh(layer_id: str) -> None:
    """Record the current UTC time for a data source."""
    now = datetime.utcnow().isoformat()
    source_timestamps[layer_id] = now


def get_source_info(layer_id: str) -> Dict[str, Any]:
    """Get full source information for a layer."""
    metadata = source_metadata.get(layer_id, {})
    timestamp = source_timestamps.get(layer_id)
    is_active = active_layers.get(layer_id, True)

    return {
        "layer_id": layer_id,
        "source": metadata.get("source", layer_id),
        "source_type": metadata.get("source_type", "unknown"),
        "description": metadata.get("description", ""),
        "last_updated": timestamp,
        "is_active": is_active,
        "freshness": "LIVE" if timestamp else "UNKNOWN"
    }


def get_all_sources_info() -> Dict[str, Dict[str, Any]]:
    """Get source info for all registered layers."""
    return {layer_id: get_source_info(layer_id) for layer_id in active_layers.keys()}


def set_layer_active(layer_id: str, active: bool) -> None:
    """Set whether a layer is active."""
    if layer_id in active_layers:
        active_layers[layer_id] = active