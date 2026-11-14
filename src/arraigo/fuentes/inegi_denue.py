"""INEGI DENUE: negocios por ubicación. Gratis, pero requiere un token que se obtiene registrándose en
https://www.inegi.org.mx/servicios/api_denue.html (formulario "Generar token"). El token va en la variable de entorno INEGI_TOKEN.
"""

from __future__ import annotations

import json
import os

from ._http import get_json

FUENTE = "INEGI, DENUE"


def negocios_cercanos(lat: float, lng: float, radio_m: int = 500, palabra: str = "todos") -> list[dict]:
    token = os.environ.get("INEGI_TOKEN")
    if not token:
        raise RuntimeError("Falta INEGI_TOKEN (token gratuito de INEGI).")
    url = f"https://www.inegi.org.mx/app/api/denue/v1/consulta/Buscar/{palabra}/{lat},{lng}/{radio_m}/{token}"
    try:
        return get_json(url)
    except json.JSONDecodeError:
        # DENUE responde con cuerpo vacío (no `[]`) cuando no hay negocios que coincidan.
        return []
