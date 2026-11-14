"""Tiempo de traslado valorizado (R3). No es un gasto de bolsillo. Función pura."""
from __future__ import annotations

from arraigo.calculos.modelos import Componente
from arraigo.calculos.supuestos import ConfigCalculos
from arraigo.calculos.traslado import redondear


def horas_traslado_mes(minutos_ida: int, config: ConfigCalculos) -> float:
    cal = config.calendario
    return minutos_ida * cal.viajes_por_dia * cal.dias_laborales_mes / 60


def tiempo_valorizado(minutos_ida: int, ingreso_mensual_mxn: int, config: ConfigCalculos) -> Componente:
    cal = config.calendario
    horas_laborales_mes = cal.dias_laborales_mes * cal.horas_laborales_dia
    ingreso_hora = ingreso_mensual_mxn / horas_laborales_mes
    horas = horas_traslado_mes(minutos_ida, config)
    valor = ingreso_hora * horas * config.tiempo.factor_valor_tiempo
    return Componente(
        monto_mxn=redondear(valor),
        fuente=config.tiempo.fuente,
        fecha_dato=config.tiempo.fecha_dato,
        supuestos=[
            f"Tu hora de trabajo vale ${ingreso_hora:,.0f} ({cal.dias_laborales_mes} días × {cal.horas_laborales_dia:g} horas al mes)",
            f"{horas:g} horas de traslado al mes ({minutos_ida} min de ida, {cal.viajes_por_dia} viajes al día)",
            f"Factor de valor del tiempo: {config.tiempo.factor_valor_tiempo:g}",
            "Es un valor de referencia, no un gasto de bolsillo",
        ],
    )
