"""Servicios mensuales estimados (R4). Es un supuesto del equipo, no una cotización. Función pura."""
from __future__ import annotations

from arraigo.calculos.modelos import Componente
from arraigo.calculos.supuestos import ConfigCalculos
from arraigo.calculos.traslado import redondear
from arraigo.schemas.inmueble import Inmueble, Operacion


def costo_servicios(inmueble: Inmueble, config: ConfigCalculos) -> Componente:
    s = config.servicios
    base = s.base_mxn + s.por_recamara_mxn * inmueble.recamaras
    desglose = {nombre: redondear(base * pct) for nombre, pct in s.desglose_pct.items()}
    total = base
    supuestos = [
        f"${s.base_mxn:,.0f} base + ${s.por_recamara_mxn:,.0f} por recámara ({inmueble.recamaras})",
        "Luz, agua, gas e internet repartidos con porcentajes fijos",
        "Estimación, no una cotización",
    ]
    if inmueble.operacion == Operacion.venta:
        extra = inmueble.precio_mxn * config.compra.mantenimiento_predial_anual_pct / 12
        total += extra
        desglose["mantenimiento_y_predial"] = redondear(extra)
        supuestos.append(
            f"Mantenimiento y predial: {config.compra.mantenimiento_predial_anual_pct * 100:g}% anual del precio, entre 12"
        )
    return Componente(
        monto_mxn=redondear(total),
        fuente=s.fuente,
        fecha_dato=s.fecha_dato,
        supuestos=supuestos,
        desglose=desglose,
    )
