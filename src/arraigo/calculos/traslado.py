"""Traslado estimado: haversine × factor de rodeo ÷ velocidad por modo (R1). Función pura, sin red."""
from __future__ import annotations

import math

from arraigo.calculos.modelos import Traslado
from arraigo.calculos.supuestos import ConfigCalculos
from arraigo.schemas.inmueble import Inmueble
from arraigo.schemas.perfil import Perfil

RADIO_TIERRA_KM = 6371.0088


class SinUbicacion(ValueError):
    """El inmueble no tiene lat/lng, así que no se puede estimar el traslado."""

    def __init__(self) -> None:
        super().__init__("sin ubicación")


def redondear(x: float) -> int:
    """Pesos o minutos enteros; .5 sube (no el redondeo bancario de `round`)."""
    return int(math.floor(x + 0.5))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


def modo_de_calculo(modo_perfil: str) -> str:
    return "transporte_publico" if modo_perfil == "mixto" else modo_perfil


def estimar_traslado(inmueble: Inmueble, perfil: Perfil, config: ConfigCalculos) -> Traslado:
    """Traslado de ida entre el inmueble y el trabajo. Lanza `SinUbicacion` si falta lat/lng."""
    if inmueble.lat is None or inmueble.lng is None:
        raise SinUbicacion()
    modo = modo_de_calculo(perfil.modo_transporte)
    d = haversine_km(inmueble.lat, inmueble.lng, perfil.destino_trabajo.lat, perfil.destino_trabajo.lng)
    ruta = d * config.traslado.factor_rodeo[modo]
    minutos = redondear(ruta / config.traslado.velocidad_kmh[modo] * 60)
    avisos: list[str] = []
    if perfil.modo_transporte == "mixto":
        avisos.append("Para modo mixto se usó el cálculo de transporte público.")
    if inmueble.ubicacion_aproximada:
        avisos.append("Ubicación aproximada: el traslado puede variar.")
    return Traslado(
        distancia_recta_km=d,
        distancia_ruta_km=ruta,
        minutos_ida=minutos,
        modo_usado=modo,
        excede_tiempo_max=minutos > perfil.tiempo_max_traslado_min,
        avisos=avisos,
    )
