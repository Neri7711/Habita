"""Normalización a 0-1 por rango percentil (spec 02, tarea 1.3)."""

from __future__ import annotations

import pandas as pd


def rango_percentil(valores: pd.Series) -> pd.Series:
    """Rango percentil reescalado a [0, 1]: el menor queda en 0 y el mayor en 1.

    Empates reciben el rango promedio. Los NaN se conservan como NaN y no cuentan.
    Si solo hay un valor distinto (o un solo dato), todos quedan en 0.5.
    """
    numeros = pd.to_numeric(valores, errors="coerce").astype(float)
    con_dato = numeros.dropna()
    salida = pd.Series(float("nan"), index=valores.index, dtype=float)
    if con_dato.empty:
        return salida
    if con_dato.nunique() == 1:
        salida[con_dato.index] = 0.5
        return salida
    rangos = con_dato.rank(method="average")
    minimo, maximo = rangos.min(), rangos.max()
    salida[con_dato.index] = (rangos - minimo) / (maximo - minimo)
    return salida
