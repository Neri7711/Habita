"""Banxico SIE API: series económicas (tasas, UDIS). Gratis, pero requiere un token que se obtiene en
https://www.banxico.org.mx/SieAPIRest/service/v1/token. El token va en la variable de entorno BANXICO_TOKEN.
"""

from __future__ import annotations

import os

from ._http import get_json

FUENTE = "Banco de México, SIE"
BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"


def dato_oportuno(serie: str) -> dict:
    token = os.environ.get("BANXICO_TOKEN")
    if not token:
        raise RuntimeError("Falta BANXICO_TOKEN (token gratuito de Banxico).")
    r = get_json(f"{BASE}/{serie}/datos/oportuno", {"token": token}, usar_cache=False)
    s = r["bmx"]["series"][0]
    return {"serie": serie, "titulo": s["titulo"], **s["datos"][0]}
