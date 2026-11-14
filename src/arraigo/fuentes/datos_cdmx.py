"""Portal Datos Abiertos CDMX (CKAN): https://datos.cdmx.gob.mx/api/3/action/

Gratis, sin token. Sirve para: catálogo de colonias, carpetas de investigación FGJ, GTFS, Ecobici, etc.
"""

from __future__ import annotations

import json

from ._http import get_json

BASE = "https://datos.cdmx.gob.mx/api/3/action"
FUENTE = "Datos Abiertos CDMX"


def buscar_datasets(texto: str, filas: int = 10) -> list[dict]:
    """Regresa [{name, title, organizacion, modificado, recursos: [{name, format, url, id}]}]."""
    r = get_json(f"{BASE}/package_search", {"q": texto, "rows": filas})["result"]["results"]
    return [
        {
            "name": d["name"],
            "title": d["title"],
            "organizacion": (d.get("organization") or {}).get("title"),
            "modificado": d.get("metadata_modified"),
            "recursos": [
                {"name": x.get("name"), "format": x.get("format"), "url": x.get("url"), "id": x.get("id")}
                for x in d.get("resources", [])
            ],
        }
        for d in r
    ]


def consultar_datastore(resource_id: str, filtros: dict | None = None, limite: int = 100) -> list[dict]:
    """Consulta filas de un recurso con 'Datastore active' sin bajar el archivo completo."""
    params: dict = {"resource_id": resource_id, "limit": limite}
    if filtros:
        params["filters"] = json.dumps(filtros, ensure_ascii=False)
    return get_json(f"{BASE}/datastore_search", params)["result"]["records"]
