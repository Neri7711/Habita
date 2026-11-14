"""Inside Airbnb: anuncios de Airbnb en CDMX (CC BY 4.0). Gratis, descarga de CSV.

Se usa como indicador indirecto de presión de gentrificación (densidad de renta corta por colonia).
"""

from __future__ import annotations

from pathlib import Path

from ._http import descargar

FECHA_CORTE = "2026-09-23"  # actualizar si sale un corte nuevo en https://insideairbnb.com/get-the-data/
URL = f"https://data.insideairbnb.com/mexico/df/mexico-city/{FECHA_CORTE}/visualisations/listings.csv"
FUENTE = f"Inside Airbnb, corte {FECHA_CORTE}"


def descargar_listings(destino_dir: Path) -> Path:
    return descargar(URL, destino_dir / f"airbnb_listings_{FECHA_CORTE}.csv")
