"""Costo real mensual: vivienda + transporte + servicios + tiempo de traslado valorizado."""

from __future__ import annotations

from arraigo.calculos import supuestos as S
from arraigo.calculos.precio_justo import precio_justo
from arraigo.calculos.traslado import estimar_traslado
from arraigo.schemas import Colonia, Inmueble, Perfil


def _componente(monto: float | None, fuente: str, supuestos: list[str], motivo: str | None = None) -> dict:
    return {"monto_mxn": None if monto is None else round(monto), "fuente": fuente, "fecha_dato": str(S.FECHA),
            "supuestos": supuestos, "motivo_no_calculable": motivo}


def mensualidad(precio: int, enganche: int, tasa_anual_pct: float = S.TASA_HIPOTECARIA_ANUAL_PCT,
                plazo_anios: int = S.PLAZO_ANIOS) -> float:
    """Cuota fija (amortización francesa)."""
    p = max(precio - enganche, 0)
    i, n = tasa_anual_pct / 12 / 100, plazo_anios * 12
    if p == 0:
        return 0.0
    return p / n if i == 0 else p * i / (1 - (1 + i) ** -n)


def _transporte(modo: str, ruta_km: float) -> tuple[float, str, list[str]]:
    n = S.DIAS_LABORALES_MES
    if modo == "auto":
        return ruta_km * 2 * n * S.AUTO_COSTO_POR_KM_MXN, S.FUENTE, [f"${S.AUTO_COSTO_POR_KM_MXN}/km", f"{n} días laborales"]
    if modo == "bici":
        return S.ECOBICI_ANUAL_MXN / 12, S.FUENTE, ["Membresía anual de Ecobici prorrateada"]
    pasajes = next(p for hasta, p in S.PASAJES_POR_DISTANCIA if ruta_km <= hasta)
    return pasajes * S.TARIFA_METRO_MXN * 2 * n, S.FUENTE_TARIFA, [
        f"{pasajes} pasaje(s) de ${S.TARIFA_METRO_MXN} por viaje", f"2 viajes al día, {n} días laborales"]


def costo_real(inmueble: Inmueble, perfil: Perfil, colonia: Colonia | None = None) -> dict:
    """Desglose mensual en MXN; cada componente con fuente y supuestos. Montos None = no calculable (con motivo)."""
    avisos = [S.AVISO_GENERAL]
    n = S.DIAS_LABORALES_MES

    # Vivienda
    hipoteca = None
    if inmueble.operacion.value == "renta":
        vivienda = _componente(inmueble.precio_mxn, f"Precio del anuncio ({inmueble.fuente})", ["Renta mensual publicada"])
    elif perfil.enganche_disponible_mxn is None:
        vivienda = _componente(None, S.FUENTE, [], "sin enganche en el perfil")
    else:
        avisos.append(S.AVISO_COMPRA)
        enganche = min(perfil.enganche_disponible_mxn, inmueble.precio_mxn)
        cuota = mensualidad(inmueble.precio_mxn, enganche)
        hipoteca = {"mensualidad_mxn": round(cuota), "enganche_mxn": enganche,
                    "monto_financiado_mxn": inmueble.precio_mxn - enganche,
                    "tasa_anual_pct": S.TASA_HIPOTECARIA_ANUAL_PCT, "plazo_anios": S.PLAZO_ANIOS}
        vivienda = _componente(cuota, S.FUENTE, [f"Tasa fija {S.TASA_HIPOTECARIA_ANUAL_PCT}% anual",
                                                 f"{S.PLAZO_ANIOS} años", f"Enganche ${enganche:,}"])

    # Servicios
    servicios = S.SERVICIOS_BASE_MXN + S.SERVICIOS_POR_RECAMARA_MXN * inmueble.recamaras
    sup_serv = [f"${S.SERVICIOS_BASE_MXN} base + ${S.SERVICIOS_POR_RECAMARA_MXN} por recámara (luz, agua, gas, internet)"]
    if inmueble.operacion.value == "venta":
        servicios += inmueble.precio_mxn * S.MANTENIMIENTO_PREDIAL_ANUAL_PCT / 12
        sup_serv.append(f"Mantenimiento y predial: {S.MANTENIMIENTO_PREDIAL_ANUAL_PCT:.1%} anual del precio")
    servicios_c = _componente(servicios, S.FUENTE, sup_serv)

    # Traslado, transporte y tiempo
    traslado = None
    if inmueble.lat is None or inmueble.lng is None:
        transporte_c = _componente(None, S.FUENTE, [], "sin ubicación")
        tiempo_c = _componente(None, S.FUENTE, [], "sin ubicación")
        horas_mes = None
    else:
        d = perfil.destino_trabajo
        traslado = estimar_traslado(inmueble.lat, inmueble.lng, d.lat, d.lng, perfil.modo_transporte,
                                    perfil.tiempo_max_traslado_min)
        if perfil.modo_transporte == "mixto":
            avisos.append(S.AVISO_MIXTO)
        if traslado["modo_usado"] == "auto":
            avisos.append(S.AVISO_AUTO)
        if inmueble.ubicacion_aproximada:
            avisos.append(S.AVISO_APROX)
        monto, fuente, sup = _transporte(traslado["modo_usado"], traslado["distancia_ruta_km"])
        transporte_c = _componente(monto, fuente, sup)
        horas_mes = traslado["minutos_ida"] * 2 * n / 60
        ingreso_hora = perfil.ingreso_mensual_mxn / (n * S.HORAS_LABORALES_DIA)
        tiempo_c = _componente(ingreso_hora * horas_mes * S.FACTOR_VALOR_TIEMPO, S.FUENTE, [
            f"Tu ingreso por hora (${ingreso_hora:,.0f}) × {horas_mes:.0f} h de traslado al mes"])

    if inmueble.fuente == "sintetico":
        avisos.append(S.AVISO_SINTETICO)

    montos = [c["monto_mxn"] for c in (vivienda, transporte_c, servicios_c)]
    monetario = sum(montos) if None not in montos else None
    real = monetario + tiempo_c["monto_mxn"] if monetario is not None and tiempo_c["monto_mxn"] is not None else None
    ingreso = perfil.ingreso_mensual_mxn

    if real is not None:
        resumen = (f"Te costaría unos ${real:,} al mes en total: ${monetario:,} en dinero "
                   f"(vivienda, transporte y servicios) más ${tiempo_c['monto_mxn']:,} del tiempo que pasas trasladándote "
                   f"({traslado['minutos_ida']} min de ida). Eso es {real / ingreso:.0%} de tu ingreso.")
    elif monetario is not None:
        resumen = f"Te costaría unos ${monetario:,} al mes en dinero; no pudimos estimar el traslado (sin ubicación)."
    else:
        resumen = "No pudimos calcular el costo mensual completo: " + ", ".join(
            c["motivo_no_calculable"] for c in (vivienda, transporte_c, tiempo_c) if c["motivo_no_calculable"]) + "."

    return {
        "inmueble_id": inmueble.id,
        "operacion": inmueble.operacion.value,
        "vivienda": vivienda,
        "transporte": transporte_c,
        "servicios": servicios_c,
        "tiempo_valorizado": tiempo_c,
        "horas_traslado_mes": None if horas_mes is None else round(horas_mes, 1),
        "costo_monetario_mxn": monetario,
        "costo_real_mxn": real,
        "pct_ingreso_monetario": None if monetario is None else round(monetario / ingreso, 3),
        "pct_ingreso_real": None if real is None else round(real / ingreso, 3),
        "traslado": traslado,
        "hipoteca": hipoteca,
        # shortcut: presupuesto_max se compara contra el precio publicado (renta mensual o precio de compra)
        "excede_presupuesto": inmueble.precio_mxn > perfil.presupuesto_max_mxn,
        "precio_justo": precio_justo(inmueble, colonia),
        "es_sintetico": inmueble.fuente == "sintetico",
        "avisos": avisos,
        "resumen": resumen,
    }
