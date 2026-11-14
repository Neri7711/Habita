"""Geocodificación con Nominatim (OpenStreetMap). Gratis, sin token, máx. 1 req/s, con caché."""

from __future__ import annotations

from ._http import get_json

URL = "https://nominatim.openstreetmap.org/search"
FUENTE = "OpenStreetMap / Nominatim (ODbL)"


def geocodificar(direccion: str) -> dict | None:
    """Regresa {lat, lng, nombre} o None si no se encontró. Limitado a México."""
    r = get_json(
        URL,
        {"q": direccion, "format": "json", "limit": 1, "countrycodes": "mx"},
        min_intervalo_s=1.1,
    )
    if not r:
        return None
    return {"lat": float(r[0]["lat"]), "lng": float(r[0]["lon"]), "nombre": r[0]["display_name"]}
