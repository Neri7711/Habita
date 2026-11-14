"""Utilidades geográficas puras (spec 02, tarea 1.2).

Los polígonos se reciben como geometrías GeoJSON (`Polygon` o `MultiPolygon`, coordenadas [lng, lat] en WGS84).

Desviación del design.md: en lugar de `shapely.STRtree` se usa punto en polígono por paridad (ray casting)
vectorizado con numpy, con prefiltro por caja envolvente sobre puntos ordenados por longitud. Motivo: `shapely`
no está instalado y `pyproject.toml` no pertenece a este carril. El resultado es el mismo para polígonos simples,
con huecos y multipolígonos; si después se agrega `shapely`, solo cambia la implementación interna.

`area_km2` usa la aproximación de grados a metros en la latitud media del anillo (proyección equirectangular
local). En CDMX (lat ~19.4) y para polígonos del tamaño de una colonia, el error frente a UTM 14N es menor a 1%.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

RADIO_TIERRA_M = 6_371_008.8
M_POR_GRADO_LAT = 110_574.0
M_POR_GRADO_LNG_ECUADOR = 111_320.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en metros sobre la esfera entre dos puntos WGS84."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_M * math.asin(math.sqrt(a))


def _poligonos(geometria: Mapping) -> list[list[list[list[float]]]]:
    """Normaliza Polygon/MultiPolygon a lista de polígonos (cada uno, lista de anillos)."""
    tipo = geometria.get("type")
    if tipo == "Polygon":
        return [geometria["coordinates"]]
    if tipo == "MultiPolygon":
        return list(geometria["coordinates"])
    raise ValueError(f"geometría no soportada: {tipo!r}")


def _dentro_de_anillos(xs: np.ndarray, ys: np.ndarray, anillos: list) -> np.ndarray:
    """Regla par-impar sobre todos los anillos de un polígono (los huecos se restan solos)."""
    dentro = np.zeros(xs.shape, dtype=bool)
    for anillo in anillos:
        a = np.asarray(anillo, dtype=float)
        x1, y1 = a[:, 0], a[:, 1]
        x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
        for ax, ay, bx, by in zip(x1, y1, x2, y2):
            if ay == by:
                continue
            cruza = (ay > ys) != (by > ys)
            x_corte = ax + (ys - ay) * (bx - ax) / (by - ay)
            dentro ^= cruza & (xs < x_corte)
    return dentro


def punto_en_poligono(lat: float, lng: float, geometria: Mapping) -> bool:
    """True si el punto cae dentro de la geometría GeoJSON."""
    xs, ys = np.array([lng], dtype=float), np.array([lat], dtype=float)
    return bool(any(_dentro_de_anillos(xs, ys, p)[0] for p in _poligonos(geometria)))


def asignar_a_colonia(puntos: pd.DataFrame, poligonos: Mapping[str, Mapping]) -> pd.Series:
    """Nombre de la colonia que contiene cada punto (columnas `lat`, `lng`), o NA si ninguna.

    Si dos polígonos se traslapan, gana el primero en el orden de `poligonos`.
    """
    resultado = pd.Series(pd.NA, index=puntos.index, dtype="object")
    if puntos.empty:
        return resultado
    lat = pd.to_numeric(puntos["lat"], errors="coerce").to_numpy(dtype=float)
    lng = pd.to_numeric(puntos["lng"], errors="coerce").to_numpy(dtype=float)
    validos = np.flatnonzero(~(np.isnan(lat) | np.isnan(lng)))
    orden = validos[np.argsort(lng[validos], kind="stable")]
    lng_ordenada = lng[orden]
    asignado = np.zeros(len(puntos), dtype=bool)
    nombres = np.full(len(puntos), None, dtype=object)

    for nombre, geometria in poligonos.items():
        for poligono in _poligonos(geometria):
            exterior = np.asarray(poligono[0], dtype=float)
            xmin, ymin = exterior.min(axis=0)
            xmax, ymax = exterior.max(axis=0)
            i0 = np.searchsorted(lng_ordenada, xmin, side="left")
            i1 = np.searchsorted(lng_ordenada, xmax, side="right")
            candidatos = orden[i0:i1]
            candidatos = candidatos[~asignado[candidatos]]
            candidatos = candidatos[(lat[candidatos] >= ymin) & (lat[candidatos] <= ymax)]
            if candidatos.size == 0:
                continue
            dentro = _dentro_de_anillos(lng[candidatos], lat[candidatos], poligono)
            elegidos = candidatos[dentro]
            nombres[elegidos] = nombre
            asignado[elegidos] = True

    resultado[:] = [n if n is not None else pd.NA for n in nombres]
    return resultado


def _area_anillo_m2(anillo: list) -> float:
    a = np.asarray(anillo, dtype=float)
    lat0 = math.radians(float(a[:, 1].mean()))
    x = a[:, 0] * M_POR_GRADO_LNG_ECUADOR * math.cos(lat0)
    y = a[:, 1] * M_POR_GRADO_LAT
    return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2


def centroide(geometria: Mapping) -> tuple[float, float]:
    """(lat, lng) del centroide de área de los anillos exteriores (fórmula del polígono plano en grados)."""
    sx = sy = sa = 0.0
    for poligono in _poligonos(geometria):
        a = np.asarray(poligono[0], dtype=float)
        x, y = a[:, 0], a[:, 1]
        x2, y2 = np.roll(x, -1), np.roll(y, -1)
        cruz = x * y2 - x2 * y
        area = cruz.sum() / 2
        if area == 0:
            continue
        sx += float(((x + x2) * cruz).sum()) / 6
        sy += float(((y + y2) * cruz).sum()) / 6
        sa += float(area)
    if sa == 0:
        a = np.asarray(_poligonos(geometria)[0][0], dtype=float)
        return float(a[:, 1].mean()), float(a[:, 0].mean())
    return sy / sa, sx / sa


def area_km2(geometria: Mapping) -> float:
    """Área aproximada en km² (anillo exterior menos huecos, sumada por polígono)."""
    total = 0.0
    for poligono in _poligonos(geometria):
        exterior, *huecos = poligono
        total += _area_anillo_m2(exterior) - sum(_area_anillo_m2(h) for h in huecos)
    return total / 1_000_000
