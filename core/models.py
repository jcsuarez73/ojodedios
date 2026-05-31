def normalize_point(source, subtype, lat=None, lon=None, metadata=None):
    return {
        "source": source,
        "type": "asset",
        "subtype": subtype,
        "lat": lat,
        "lon": lon,
        "metadata": metadata or {}
    }
