"""Polígonos de colonias para la spec 02.

La spec 01 dejó centroides manuales y no polígonos (`pipeline/colonias.py`). Aquí se usa el catálogo de
"Colonias CDMX" del IECM 2019 (Datos Abiertos CDMX, GeoJSON en WGS84, 1,814 unidades; `data/raw/colonias_iecm_2019.geojson`).

El IECM divide muchas colonias en unidades electorales ("ROMA NORTE I", "ROMA NORTE II", ...). Una colonia piloto se
arma como la unión de sus unidades, buscando en la misma alcaldía:
1. unidades cuyo nombre normalizado es igual al de la colonia, o igual más un número romano (I, II, ...);
2. si no hay, lo mismo quitando "seccion" al final ("Escandón I Sección" -> "ESCANDON I");
3. si aun así no hay: la unidad que contiene el centroide manual (aproximación; p. ej. "Del Valle Centro" no
   existe con ese nombre en el IECM, que la divide en DEL VALLE I-VII).
Si hay coincidencia por nombre pero el centroide manual (~300 m de error) cae fuera, se acepta el nombre y se anota.
El método usado queda registrado por colonia (`metodo`) para el reporte.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from arraigo.pipeline.colonias import RAIZ, normalizar
from arraigo.pipeline.enriquecer.geo import area_km2, punto_en_poligono

RUTA_IECM = RAIZ / "data" / "raw" / "colonias_iecm_2019.geojson"
FUENTE_IECM = "IECM, Colonias CDMX 2019 (Datos Abiertos CDMX)"
_ROMANO = r"(i|ii|iii|iv|v|vi|vii|viii|ix|x)"


@dataclass
class Unidad:
    id: str
    nombre: str
    alcaldia: str
    geometria: dict
    area_km2: float = 0.0


@dataclass
class ColoniaPoligono:
    nombre: str
    unidades: list[str] = field(default_factory=list)
    metodo: str = ""  # "nombre", "nombre_sin_seccion", "centroide" o "sin_poligono"


def cargar_unidades(ruta: Path = RUTA_IECM) -> list[Unidad]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    unidades = []
    for f in datos["features"]:
        p, g = f["properties"], f.get("geometry")
        if not g:
            continue
        unidades.append(Unidad(str(p["ID"]), p["NOMUT"], p["NOMDT"], g, area_km2(g)))
    return unidades


def _por_nombre(unidades: list[Unidad], base: str, alcaldia: str) -> list[Unidad]:
    patron = re.compile(rf"^{re.escape(base)}( {_ROMANO})?$")
    return [u for u in unidades if normalizar(u.alcaldia) == alcaldia and patron.match(normalizar(u.nombre))]


def mapear_colonia(unidades: list[Unidad], nombre: str, alcaldia: str, lat: float, lng: float) -> ColoniaPoligono:
    base, alc = normalizar(nombre), normalizar(alcaldia)
    for metodo, b in (("nombre", base), ("nombre_sin_seccion", re.sub(r"\s+seccion$", "", base))):
        encontradas = _por_nombre(unidades, b, alc)
        if encontradas:
            if not any(punto_en_poligono(lat, lng, u.geometria) for u in encontradas):
                metodo += " (centroide manual fuera)"
            return ColoniaPoligono(nombre, [u.id for u in encontradas], metodo)
    contiene = [u for u in unidades if punto_en_poligono(lat, lng, u.geometria)]
    if contiene:
        return ColoniaPoligono(nombre, [contiene[0].id], "centroide")
    return ColoniaPoligono(nombre, [], "sin_poligono")
