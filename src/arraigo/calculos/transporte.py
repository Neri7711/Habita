"""Costo mensual de transporte con tarifas oficiales SEMOVI (R2). Función pura."""
from __future__ import annotations

from arraigo.calculos.modelos import Componente, Traslado
from arraigo.calculos.supuestos import ConfigCalculos, Tarifa, TarifasSemovi
from arraigo.calculos.traslado import redondear
from arraigo.schemas.colonia import Colonia


def _clave_tarifa(colonia: Colonia | None, config: ConfigCalculos, tarifas: TarifasSemovi) -> tuple[str, bool]:
    """Clave de tarifa según la estación más cercana de la colonia; (clave, es_la_por_defecto)."""
    defecto = config.transporte_publico.tarifa_por_defecto
    estaciones = colonia.estaciones_transporte_cercanas.valor if colonia else None
    if estaciones:
        ordenadas = sorted(estaciones, key=lambda e: (e.distancia_m is None, e.distancia_m or 0.0))
        clave = config.transporte_publico.mapeo_estacion.get(ordenadas[0].tipo.value)
        if clave and clave in tarifas.tarifas:
            return clave, False
    return defecto, True


def _nombre(clave: str) -> str:
    return clave.replace("_", " ")


def costo_transporte_mensual(
    traslado: Traslado | None,
    modo_perfil: str,
    colonia: Colonia | None,
    config: ConfigCalculos,
    tarifas: TarifasSemovi,
) -> Componente:
    cal = config.calendario
    if modo_perfil == "bici":
        t = tarifas.tarifas["ecobici_anual"]
        return Componente(
            monto_mxn=redondear(t.mxn / 12),
            fuente=t.url,
            fecha_dato=t.fecha_vigencia,
            supuestos=[f"Plan anual de Ecobici (${t.mxn:,.0f}) dividido entre 12 meses"],
        )
    if traslado is None:
        return Componente(
            monto_mxn=None,
            fuente="no calculable",
            fecha_dato=config.traslado.fecha_dato,
            motivo_no_calculable="sin ubicación",
        )
    if modo_perfil == "auto":
        c = config.auto
        monto = traslado.distancia_ruta_km * cal.viajes_por_dia * cal.dias_laborales_mes * c.costo_por_km_mxn
        return Componente(
            monto_mxn=redondear(monto),
            fuente=c.fuente,
            fecha_dato=c.fecha_dato,
            supuestos=[
                f"${c.costo_por_km_mxn:g} por kilómetro ({c.nota})",
                f"{cal.viajes_por_dia} viajes al día, {cal.dias_laborales_mes} días laborales al mes",
            ],
        )
    # transporte_publico o mixto
    clave, es_defecto = _clave_tarifa(colonia, config, tarifas)
    tarifa: Tarifa = tarifas.tarifas[clave]
    pasajes = config.pasajes.pasajes_para(traslado.distancia_ruta_km)
    monto = pasajes * tarifa.mxn * cal.viajes_por_dia * cal.dias_laborales_mes
    supuestos = [
        f"{pasajes} pasaje(s) por viaje, según la distancia de ruta",
        f"Tarifa de {_nombre(clave)}: ${tarifa.mxn:g} por pasaje",
        f"{cal.viajes_por_dia} viajes al día, {cal.dias_laborales_mes} días laborales al mes",
    ]
    if es_defecto:
        supuestos.append(f"Sin estaciones cercanas en los datos: se usó la tarifa por defecto ({_nombre(clave)})")
    return Componente(monto_mxn=redondear(monto), fuente=tarifa.url, fecha_dato=tarifa.fecha_vigencia, supuestos=supuestos)
