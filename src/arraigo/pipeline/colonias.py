"""Catálogo de colonias piloto y centroides.

Los centroides son manuales (columnas lat/lng de colonias_piloto.csv): para 13 colonias no vale la pena
el GeoJSON + shapely. shortcut: centroides aproximados a mano (~300 m); si se agregan muchas colonias, calcularlos del GeoJSON del IECM.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CATALOGO_CSV = RAIZ / "data" / "raw" / "colonias_piloto.csv"
FUENTE_CENTROIDE = "centroide manual aproximado del equipo (data/raw/colonias_piloto.csv)"
FECHA_CENTROIDE = date(2026, 11, 14)


def normalizar(nombre: str) -> str:
    """Minúsculas, sin acentos, sin prefijo 'col.'/'colonia', espacios simples."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    texto = re.sub(r"^\s*(col\.?|colonia)\s+", "", sin_acentos.lower())
    return " ".join(texto.split())


def cargar_catalogo(ruta: Path = CATALOGO_CSV) -> dict[str, dict]:
    """{nombre_normalizado: {colonia, alcaldia, lat, lng}}."""
    with ruta.open(encoding="utf-8", newline="") as f:
        return {
            normalizar(fila["colonia"]): {
                "colonia": fila["colonia"],
                "alcaldia": fila["alcaldia"],
                "lat": float(fila["lat"]),
                "lng": float(fila["lng"]),
            }
            for fila in csv.DictReader(f)
        }


def centroides(catalogo: dict[str, dict]) -> dict[str, tuple[float, float]]:
    """{nombre_canonico: (lat, lng)} para el contexto de validación de Inmueble."""
    return {c["colonia"]: (c["lat"], c["lng"]) for c in catalogo.values()}
