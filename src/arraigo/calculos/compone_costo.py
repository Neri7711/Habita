"""Costo real mensual: vivienda + transporte + servicios + tiempo valorizado (R6). Función pura."""
from __future__ import annotations

from arraigo.calculos.hipoteca import mensualidad_compra
from arraigo.calculos.modelos import Componente, CostoReal, Hipoteca, TasaReferencia, Traslado
from arraigo.calculos.banda_precio import AVISO_SINTETICO, evaluar_precio_justo
from arraigo.calculos.servicios import costo_servicios
from arraigo.calculos.supuestos import ConfigCalculos, TarifasSemovi, tasa_respaldo
from arraigo.calculos.tiempo import horas_traslado_mes, tiempo_valorizado
from arraigo.calculos.traslado import SinUbicacion, estimar_traslado
from arraigo.calculos.transporte import costo_transporte_mensual
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble, Operacion
from arraigo.schemas.perfil import Perfil

AVISO_GENERAL = "Estimación con supuestos; revisa los detalles antes de decidir."
AVISO_AUTO = "No incluye estacionamiento, seguro ni tenencia."


def _no_calculable(motivo: str, config: ConfigCalculos) -> Componente:
    return Componente(
        monto_mxn=None, fuente="no calculable", fecha_dato=config.calendario.fecha_dato, motivo_no_calculable=motivo
    )


def _vivienda(
    inmueble: Inmueble, perfil: Perfil, config: ConfigCalculos, tasa: TasaReferencia | None
) -> tuple[Componente, Hipoteca | None, int | None]:
    """Componente de vivienda, hipoteca (solo compra) y enganche inicial."""
    if inmueble.operacion == Operacion.renta:
        return (
            Componente(
                monto_mxn=inmueble.precio_mxn,
                fuente=f"Precio del anuncio ({inmueble.fuente})",
                fecha_dato=inmueble.fecha_captura,
                supuestos=["Renta mensual del anuncio"],
            ),
            None,
            None,
        )
    if perfil.enganche_disponible_mxn is None:
        return _no_calculable("sin enganche", config), None, None
    tasa = tasa or tasa_respaldo(config)
    h = mensualidad_compra(inmueble.precio_mxn, perfil.enganche_disponible_mxn, tasa, config)
    comp = Componente(
        monto_mxn=h.mensualidad_mxn,
        fuente=h.fuente_tasa if h.es_tasa_respaldo else f"{h.fuente_tasa} (tasa de referencia)",
        fecha_dato=h.fecha_tasa,
        supuestos=[
            f"Tasa anual {h.tasa_anual_pct:g}% (referencia {h.tasa_referencia_pct:g}% + {config.compra.spread_sobre_tiie_pp:g} puntos)",
            f"Plazo de {h.plazo_anios} años",
            f"Enganche de ${h.enganche_mxn:,.0f} y crédito de ${h.monto_financiado_mxn:,.0f}",
        ],
    )
    return comp, h, min(h.enganche_mxn, inmueble.precio_mxn)


def _pct(monto: int | None, ingreso: int) -> float | None:
    return None if monto is None else round(monto / ingreso * 100, 1)


def _resumen(c: dict) -> str:
    if c["costo_real"] is None:
        faltan = [n for n in ("vivienda", "transporte", "servicios", "tiempo_valorizado") if c[n].monto_mxn is None]
        motivos = ", ".join(f"{n.replace('_', ' ')} ({c[n].motivo_no_calculable})" for n in faltan)
        partes = [f"No pudimos calcular el costo real completo: falta {motivos}."]
        if c["vivienda"].monto_mxn is not None:
            partes.append(f"Solo sabemos que {c['nombre_vivienda']} es de ${c['vivienda'].monto_mxn:,} al mes.")
        return " ".join(partes)
    texto = (
        f"Vivir aquí cuesta ${c['monetario']:,} al mes de bolsillo ({c['nombre_vivienda']}, transporte y servicios). "
        f"Si valoras tu tiempo de traslado ({c['horas']:g} horas al mes), el costo real sube a ${c['costo_real']:,}."
    )
    if c["enganche"] is not None:
        texto += f" Además necesitas ${c['enganche']:,} de enganche, que no está en el costo mensual."
    return texto


def calcular_costo_real(
    inmueble: Inmueble,
    perfil: Perfil,
    colonia: Colonia | None,
    config: ConfigCalculos,
    tarifas: TarifasSemovi,
    tasa: TasaReferencia | None = None,
) -> CostoReal:
    """Costo mensual de vivir en `inmueble` con el `perfil` dado, con desglose, supuestos y avisos.

    Interfaz para la herramienta `costo_real` de la spec 05 (vía `arraigo.calculos.costo_real`, que carga
    la configuración). Determinista y sin red: la tasa de Banxico llega en `tasa` (si es None se usa la de
    respaldo). Cada componente es un `Componente` con `monto_mxn` entero, `fuente`, `fecha_dato` y supuestos;
    si falta un dato el componente queda con `monto_mxn=None` y su motivo, y no hay total.
    """
    try:
        traslado: Traslado | None = estimar_traslado(inmueble, perfil, config)
    except SinUbicacion:
        traslado = None

    vivienda, hipoteca, enganche = _vivienda(inmueble, perfil, config, tasa)
    transporte = costo_transporte_mensual(traslado, perfil.modo_transporte, colonia, config, tarifas)
    servicios = costo_servicios(inmueble, config)
    if traslado is None:
        tiempo = _no_calculable("sin ubicación", config)
        horas = None
    else:
        tiempo = tiempo_valorizado(traslado.minutos_ida, perfil.ingreso_mensual_mxn, config)
        horas = horas_traslado_mes(traslado.minutos_ida, config)

    base = [vivienda.monto_mxn, transporte.monto_mxn, servicios.monto_mxn]
    monetario = None if None in base else sum(base)
    real = None if monetario is None or tiempo.monto_mxn is None else monetario + tiempo.monto_mxn

    es_venta = inmueble.operacion == Operacion.venta
    pago_excede = vivienda.monto_mxn is not None and (
        vivienda.monto_mxn > config.compra.pago_max_pct_ingreso * perfil.ingreso_mensual_mxn
    )
    precio_justo = evaluar_precio_justo(inmueble, colonia, config)
    es_sintetico = inmueble.fuente == "sintetico"

    avisos = [AVISO_GENERAL]
    if es_venta:
        avisos.extend(hipoteca.avisos if hipoteca else [])
        avisos.append("El enganche no está incluido en el costo mensual.")
    if traslado:
        avisos.extend(traslado.avisos)
        if traslado.excede_tiempo_max:
            avisos.append(f"El traslado de {traslado.minutos_ida} min supera tu máximo de {perfil.tiempo_max_traslado_min} min.")
    if perfil.modo_transporte == "auto":
        avisos.append(AVISO_AUTO)
    if inmueble.ubicacion_aproximada and traslado is None:
        avisos.append("Ubicación aproximada: el traslado puede variar.")
    if pago_excede:
        avisos.append(
            f"El pago de vivienda supera el {config.compra.pago_max_pct_ingreso * 100:g}% de tu ingreso mensual (referencia general)."
        )
    excede_presupuesto = inmueble.precio_mxn > perfil.presupuesto_max_mxn
    if excede_presupuesto:
        avisos.append("El precio supera tu presupuesto máximo.")
    if es_sintetico:
        avisos.append(AVISO_SINTETICO)
    avisos = list(dict.fromkeys(avisos))

    resumen = _resumen(
        {
            "vivienda": vivienda, "transporte": transporte, "servicios": servicios, "tiempo_valorizado": tiempo,
            "costo_real": real, "monetario": monetario, "horas": horas, "enganche": enganche,
            "nombre_vivienda": "la mensualidad de compra" if es_venta else "la renta",
        }
    )
    return CostoReal(
        inmueble_id=inmueble.id,
        operacion=inmueble.operacion.value,
        vivienda=vivienda,
        transporte=transporte,
        servicios=servicios,
        tiempo_valorizado=tiempo,
        horas_traslado_mes=horas,
        costo_monetario_mxn=monetario,
        costo_real_mxn=real,
        pct_ingreso_monetario=_pct(monetario, perfil.ingreso_mensual_mxn),
        pct_ingreso_real=_pct(real, perfil.ingreso_mensual_mxn),
        traslado=traslado,
        hipoteca=hipoteca,
        enganche_inicial_mxn=enganche,
        excede_presupuesto=excede_presupuesto,
        pago_excede_ingreso=pago_excede,
        precio_justo=precio_justo,
        es_sintetico=es_sintetico,
        avisos=avisos,
        resumen=resumen,
    )
