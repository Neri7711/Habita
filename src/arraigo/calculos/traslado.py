"""Traslado estimado: haversine × factor de rodeo ÷ velocidad por modo."""

from __future__ import annotations

import math

from arraigo.calculos import supuestos as S

RADIO_TIERRA_KM = 6371.0088


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2
    return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


def estimar_traslado(lat: float, lng: float, destino_lat: float, destino_lng: float,
                     modo: str, tiempo_max_min: int) -> dict:
    modo_usado = "transporte_publico" if modo == "mixto" else modo
    recta = haversine_km(lat, lng, destino_lat, destino_lng)
    ruta = recta * S.FACTOR_RODEO[modo_usado]
    minutos = round(ruta / S.VELOCIDAD_KMH[modo_usado] * 60)
    return {
        "distancia_recta_km": round(recta, 2),
        "distancia_ruta_km": round(ruta, 2),
        "minutos_ida": minutos,
        "modo_usado": modo_usado,
        "excede_tiempo_max": minutos > tiempo_max_min,
    }
