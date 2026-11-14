"""Puntos de comunidad desde OpenStreetMap vía Overpass API. Gratis, sin token."""

from __future__ import annotations

from ._http import get_json

URL = "https://overpass-api.de/api/interpreter"
ESPEJOS = ("https://overpass.private.coffee/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter")
FUENTE = "OpenStreetMap / Overpass (ODbL)"

# categoria -> lista de (clave, valor) de etiquetas OSM
CATEGORIAS: dict[str, list[tuple[str, str]]] = {
    "mercado": [("amenity", "marketplace")],
    "parque": [("leisure", "park")],
    "centro_cultural": [("amenity", "arts_centre"), ("amenity", "community_centre"), ("amenity", "library")],
    "estacion_transporte": [("railway", "station"), ("public_transport", "station")],
}


def puntos_cercanos(lat: float, lng: float, radio_m: int = 800) -> list[dict]:
    """Regresa [{categoria, nombre, lat, lng}] alrededor de un punto."""
    # Agrupar por clave con regex: menos cláusulas = consulta más ligera (los servidores públicos dan 502 con muchas)
    por_clave: dict[str, set[str]] = {}
    for etiquetas in CATEGORIAS.values():
        for k, v in etiquetas:
            por_clave.setdefault(k, set()).add(v)
    partes = [
        f'nwr["{k}"~"^({"|".join(sorted(vs))})$"](around:{radio_m},{lat},{lng});'
        for k, vs in por_clave.items()
    ]
    consulta = f"[out:json][timeout:25];({''.join(partes)});out center tags;"
    ultimo_error: Exception | None = None
    for url in (URL, *ESPEJOS):
        try:
            elementos = get_json(url, data={"data": consulta}, min_intervalo_s=1.0)["elements"]
            break
        except Exception as e:  # servidores públicos se saturan seguido: probar el siguiente espejo
            ultimo_error = e
    else:
        raise RuntimeError("Ningún servidor Overpass respondió") from ultimo_error

    salida = []
    for e in elementos:
        tags = e.get("tags", {})
        categoria = next(
            (c for c, etiquetas in CATEGORIAS.items() if any(tags.get(k) == v for k, v in etiquetas)),
            None,
        )
        centro = e.get("center", e)
        if categoria and "lat" in centro:
            salida.append(
                {"categoria": categoria, "nombre": tags.get("name"), "lat": centro["lat"], "lng": centro["lon"]}
            )
    return salida
