"""Precio justo: precio por m² contra la mediana de la colonia (R7). Función pura."""
from __future__ import annotations

import re

from arraigo.calculos.modelos import PrecioJusto
from arraigo.calculos.supuestos import ConfigCalculos
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble, Operacion

AVISO_SINTETICO = "Este anuncio es sintético (de prueba), no un inmueble real."
AVISO_MEDIANA_SINTETICA = "La mediana de referencia viene de anuncios sintéticos (de prueba)."


def _n_anuncios(fuente: str | None) -> int | None:
    """Número de anuncios, si la fuente de la mediana lo menciona (`n=12` o `12 anuncios`)."""
    if not fuente:
        return None
    m = re.search(r"n\s*=\s*(\d+)", fuente) or re.search(r"(\d+)\s+anuncios", fuente)
    return int(m.group(1)) if m else None


def _no_evaluable(motivo: str, sintetico: bool) -> PrecioJusto:
    texto = f"No podemos decir si el precio es justo: {motivo}."
    if sintetico:
        texto += f" {AVISO_SINTETICO}"
    return PrecioJusto(banda="no_evaluable", es_sintetico=sintetico, explicacion=texto, motivo_no_evaluable=motivo)


def evaluar_precio_justo(inmueble: Inmueble, colonia: Colonia | None, config: ConfigCalculos) -> PrecioJusto:
    """Clasifica el precio por m² del anuncio en `sospechosamente_barato`, `justo` o `caro`.

    Interfaz para la herramienta `precio_justo` de la spec 05 (no necesita perfil). Usa la mediana de la
    colonia para la misma operación, la misma que usa el antifraude (spec 04), sin recalcularla.
    Sin `m2` o sin mediana devuelve `no_evaluable` con el motivo.
    """
    sintetico = inmueble.fuente == "sintetico"
    if not inmueble.m2:
        return _no_evaluable("el anuncio no indica los metros cuadrados", sintetico)
    if colonia is None:
        return _no_evaluable("no hay datos de la colonia", sintetico)
    dato = colonia.precio_m2_renta_mediana if inmueble.operacion == Operacion.renta else colonia.precio_m2_venta_mediana
    if dato.valor is None or dato.valor <= 0:
        return _no_evaluable(f"la colonia {colonia.nombre} no tiene un precio de referencia por m²", sintetico)

    precio_m2 = inmueble.precio_mxn / inmueble.m2
    razon = precio_m2 / dato.valor
    cfg = config.precio_justo
    if razon < cfg.umbral_sospechosamente_barato:
        banda = "sospechosamente_barato"
    elif razon > cfg.umbral_caro:
        banda = "caro"
    else:
        banda = "justo"

    fuente = f"{dato.fuente}, {colonia.nombre}, {dato.fecha_dato}"
    mediana_sintetica = "sint" in (dato.fuente or "").lower()
    sintetico_total = sintetico or mediana_sintetica
    diff = (razon - 1) * 100
    comparacion = (
        f"El anuncio cuesta ${precio_m2:,.0f} por m² y la mediana de {colonia.nombre} es ${dato.valor:,.0f} por m² "
        f"({abs(diff):.0f}% {'más' if diff >= 0 else 'menos'})."
    )
    if banda == "justo":
        texto = f"El precio está dentro de lo normal para la colonia. {comparacion}"
    elif banda == "caro":
        texto = f"El precio está por encima de lo normal para la colonia. {comparacion}"
    else:
        texto = (
            f"El precio está muy por debajo de lo normal para la colonia. {comparacion} "
            "Puede ser una oportunidad o una señal de fraude; revisa la evaluación antifraude antes de decidir."
        )
    texto += f" Referencia: {fuente}."
    if sintetico:
        texto += f" {AVISO_SINTETICO}"
    if mediana_sintetica:
        texto += f" {AVISO_MEDIANA_SINTETICA}"
    return PrecioJusto(
        banda=banda,
        precio_m2=precio_m2,
        mediana_m2=dato.valor,
        razon=razon,
        diferencia_pct=diff,
        n_anuncios_mediana=_n_anuncios(dato.fuente),
        fuente_referencia=fuente,
        es_sintetico=sintetico_total,
        explicacion=texto,
    )
