"""Mensualidad de compra con amortización francesa (cuota fija) (R5). Función pura: la tasa llega como parámetro."""
from __future__ import annotations

from arraigo.calculos.modelos import Hipoteca, TasaReferencia
from arraigo.calculos.supuestos import ConfigCalculos
from arraigo.calculos.traslado import redondear

AVISO_HIPOTECA = "Estimación, no es asesoría hipotecaria; no incluye comisiones, seguros ni gastos de escrituración."
AVISO_RESPALDO = "Tasa de respaldo, no es dato de Banxico."
AVISO_ENGANCHE_MINIMO = "Enganche menor al mínimo habitual; el crédito podría no aprobarse."
AVISO_ENGANCHE_TOTAL = "El enganche cubre todo el precio: no hace falta crédito y la mensualidad es 0."


def cuota_fija(monto: float, tasa_anual_pct: float, plazo_anios: int) -> float:
    """`P·i / (1 − (1+i)^−n)`; con tasa 0 es `P / n`; con monto 0 es 0."""
    if monto <= 0:
        return 0.0
    n = plazo_anios * 12
    i = tasa_anual_pct / 12 / 100
    if i == 0:
        return monto / n
    return monto * i / (1 - (1 + i) ** -n)


def mensualidad_compra(
    precio_mxn: int,
    enganche_mxn: int,
    tasa: TasaReferencia,
    config: ConfigCalculos,
    plazo_anios: int | None = None,
) -> Hipoteca:
    c = config.compra
    plazo = plazo_anios or c.plazo_anios
    tasa_anual = tasa.tasa_pct + c.spread_sobre_tiie_pp
    financiado = max(precio_mxn - enganche_mxn, 0)
    avisos = [AVISO_HIPOTECA]
    if tasa.es_respaldo:
        avisos.append(AVISO_RESPALDO)
    if enganche_mxn >= precio_mxn:
        avisos.append(AVISO_ENGANCHE_TOTAL)
    elif enganche_mxn < c.enganche_minimo_pct * precio_mxn:
        avisos.append(AVISO_ENGANCHE_MINIMO)
    return Hipoteca(
        mensualidad_mxn=redondear(cuota_fija(financiado, tasa_anual, plazo)),
        enganche_mxn=enganche_mxn,
        monto_financiado_mxn=financiado,
        tasa_anual_pct=tasa_anual,
        tasa_referencia_pct=tasa.tasa_pct,
        plazo_anios=plazo,
        fuente_tasa=tasa.fuente,
        fecha_tasa=tasa.fecha,
        es_tasa_respaldo=tasa.es_respaldo,
        avisos=avisos,
    )
