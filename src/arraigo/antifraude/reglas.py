"""Una función pura por regla. Pesos, umbrales y frases vienen de la configuración."""
from __future__ import annotations

import re
from collections.abc import Callable

from arraigo.antifraude.modelos import ContextoAntifraude, NoEvaluable, Senal
from arraigo.antifraude.texto import (
    buscar_frase,
    extraer_telefonos,
    normalizar,
    ocultar_telefono,
    prefijo_telefono,
)
from arraigo.schemas.colonia import Dato
from arraigo.schemas.inmueble import Inmueble

Resultado = Senal | NoEvaluable | None

# Texto corto de cada regla para el resumen ("La más importante: ...").
TITULOS: dict[str, str] = {
    "precio_muy_bajo": "el precio es menos de la mitad de lo normal en la colonia",
    "precio_algo_bajo": "el precio es bastante más bajo que el de otros anuncios de la zona",
    "deposito_antes_de_visitar": "piden dinero antes de que veas el lugar",
    "sin_direccion": "no dice en qué calle está",
    "solo_whatsapp": "solo se puede contactar por mensaje",
    "whatsapp_extranjero": "el número de contacto es de otro país",
    "descripcion_duplicada": "el mismo texto aparece en otro anuncio",
    "urgencia_presion": "te presionan para decidir rápido",
    "sin_fotos_ni_visita": "no hay fotos ni forma de visitarlo",
    "m2_inconsistente": "el tamaño del anuncio no coincide con el de su descripción",
    "sin_url_origen": "no tenemos el enlace del anuncio original",
}


def _senal(regla: str, ctx: ContextoAntifraude, evidencia: str, explicacion: str) -> Senal | None:
    peso = ctx.config.peso(regla)
    if peso <= 0:  # regla desactivada en la configuración
        return None
    return Senal(regla=regla, puntos=peso, evidencia=evidencia, explicacion=explicacion)


def _pesos(n: float) -> str:
    return f"${n:,.0f}"


def mediana_de(inmueble: Inmueble, ctx: ContextoAntifraude) -> Dato[float] | None:
    dato = ctx.medianas_m2.get((normalizar(inmueble.colonia), inmueble.operacion))
    return dato if dato is not None and dato.valor else None


def _ratio_precio(inmueble: Inmueble, ctx: ContextoAntifraude, regla: str) -> tuple[float, float, float] | NoEvaluable:
    """(precio por m2, mediana, ratio) o NoEvaluable."""
    if not inmueble.m2:
        return NoEvaluable(regla=regla, motivo="falta el tamaño (m2)")
    mediana = mediana_de(inmueble, ctx)
    if mediana is None:
        return NoEvaluable(regla=regla, motivo="la colonia no tiene mediana de precio")
    precio_m2 = inmueble.precio_mxn / inmueble.m2
    return precio_m2, mediana.valor, precio_m2 / mediana.valor


def _evidencia_precio(inmueble: Inmueble, precio_m2: float, mediana: float, ratio: float) -> str:
    return (
        f"Cuesta {_pesos(precio_m2)}/m²; lo típico en {inmueble.colonia} es {_pesos(mediana)}/m² "
        f"({ratio:.0%})."
    )


def precio_muy_bajo(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    r = _ratio_precio(inmueble, ctx, "precio_muy_bajo")
    if isinstance(r, NoEvaluable):
        return r
    precio_m2, mediana, ratio = r
    if ratio < ctx.config.param("precio_muy_bajo", "ratio_max", 0.5):
        return _senal(
            "precio_muy_bajo", ctx, _evidencia_precio(inmueble, precio_m2, mediana, ratio),
            "Cuesta menos de la mitad de lo normal en esta colonia. Un precio así casi nunca es real.",
        )
    return None


def precio_algo_bajo(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    r = _ratio_precio(inmueble, ctx, "precio_algo_bajo")
    if isinstance(r, NoEvaluable):
        return r
    precio_m2, mediana, ratio = r
    minimo = ctx.config.param("precio_algo_bajo", "ratio_min", 0.5)
    maximo = ctx.config.param("precio_algo_bajo", "ratio_max", 0.7)
    if minimo <= ratio < maximo:
        return _senal(
            "precio_algo_bajo", ctx, _evidencia_precio(inmueble, precio_m2, mediana, ratio),
            "Es bastante más barato que otros anuncios de la zona. Pregunta por qué.",
        )
    return None


def deposito_antes_de_visitar(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    texto = normalizar(inmueble.descripcion)
    cfg = lambda k: ctx.config.param("deposito_antes_de_visitar", k, [])  # noqa: E731
    frase = buscar_frase(texto, cfg("frases_directas"))
    if frase is None and buscar_frase(texto, cfg("frases_visita")) is None:
        # Pago sin ninguna mención de visita. El depósito normal del contrato no coincide con estos patrones.
        frase = buscar_frase(texto, cfg("frases_pago"))
    if frase:
        return _senal(
            "deposito_antes_de_visitar", ctx, f"El anuncio dice: «{frase}».",
            "Te piden dinero antes de que veas el lugar. No pagues nada hasta visitarlo y conocer a quien lo renta.",
        )
    return None


def sin_direccion(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    if not inmueble.ubicacion_aproximada:
        return None
    texto = normalizar(inmueble.descripcion)
    if buscar_frase(texto, ctx.config.param("sin_direccion", "patrones_direccion", [])):
        return None
    return _senal(
        "sin_direccion", ctx, "Sin calle ni referencia.",
        "No dice en qué calle está. Pide la dirección exacta antes de seguir.",
    )


def solo_whatsapp(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    texto = normalizar(inmueble.descripcion)
    frase = buscar_frase(texto, ctx.config.param("solo_whatsapp", "frases", []))
    if frase is None:
        return None
    if buscar_frase(texto, ctx.config.param("solo_whatsapp", "excepciones", [])):
        return None
    return _senal(
        "solo_whatsapp", ctx, f"El anuncio dice: «{frase}».",
        "Solo se puede hablar por mensaje. Pide una llamada o ver el lugar en persona.",
    )


def whatsapp_extranjero(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    local = ctx.config.param("whatsapp_extranjero", "prefijo_local", "52")
    for tel in extraer_telefonos(inmueble.descripcion):
        if not prefijo_telefono(tel).startswith(local):
            return _senal(
                "whatsapp_extranjero", ctx, f"Número de contacto: {ocultar_telefono(tel)}.",
                "El número es de otro país. Quien renta un lugar en CDMX normalmente tiene un número mexicano.",
            )
    return None


def descripcion_duplicada(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    p = lambda k, d: ctx.config.param("descripcion_duplicada", k, d)  # noqa: E731
    hallado = ctx.indice_duplicados.buscar(
        inmueble.id, inmueble.colonia, inmueble.precio_mxn, inmueble.descripcion,
        jaccard_min=p("jaccard_min", 0.8), min_palabras=p("min_palabras", 6),
        dif_precio_max=p("dif_precio_max", 0.10),
    )
    if hallado:
        otro, sim = hallado
        return _senal(
            "descripcion_duplicada", ctx, f"Texto casi igual ({sim:.0%}) al del anuncio {otro}.",
            "El mismo texto aparece en otro anuncio de otra zona o con otro precio. Es común en anuncios copiados.",
        )
    return None


def urgencia_presion(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    frase = buscar_frase(normalizar(inmueble.descripcion), ctx.config.param("urgencia_presion", "frases", []))
    if frase:
        return _senal(
            "urgencia_presion", ctx, f"El anuncio dice: «{frase}».",
            "Te apuran para decidir rápido. Tómate tu tiempo.",
        )
    return None


def sin_fotos_ni_visita(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    frase = buscar_frase(normalizar(inmueble.descripcion), ctx.config.param("sin_fotos_ni_visita", "frases", []))
    if frase:
        return _senal(
            "sin_fotos_ni_visita", ctx, f"El anuncio dice: «{frase}».",
            "No hay fotos ni forma de visitarlo. Sin ver el lugar no hay manera de comprobar que existe.",
        )
    return None


def m2_inconsistente(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    """El tamaño del campo `m2` difiere del que dice la descripción (el precio por m2 se vería artificialmente bajo)."""
    if not inmueble.m2:
        return NoEvaluable(regla="m2_inconsistente", motivo="falta el tamaño (m2)")
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|metros)", normalizar(inmueble.descripcion))
    if not m:
        return NoEvaluable(regla="m2_inconsistente", motivo="la descripción no menciona el tamaño")
    en_texto = float(m.group(1).replace(",", "."))
    tolerancia = ctx.config.param("m2_inconsistente", "tolerancia", 0.15)
    if en_texto > 0 and abs(inmueble.m2 - en_texto) / en_texto > tolerancia:
        return _senal(
            "m2_inconsistente", ctx, f"El anuncio indica {inmueble.m2:g} m² pero el texto dice {en_texto:g} m².",
            "El tamaño que aparece no coincide con el de la descripción. Pide los metros exactos y confírmalos al visitarlo.",
        )
    return None


def sin_url_origen(inmueble: Inmueble, ctx: ContextoAntifraude) -> Resultado:
    prefijo = ctx.config.param("sin_url_origen", "prefijo_fuente", "captura_manual")
    if inmueble.fuente.startswith(prefijo) and inmueble.url_origen is None:
        return _senal(
            "sin_url_origen", ctx, "El anuncio capturado a mano no trae enlace.",
            "No tenemos el enlace del anuncio original, así que no se puede revisar.",
        )
    return None


REGISTRO: dict[str, Callable[[Inmueble, ContextoAntifraude], Resultado]] = {
    "precio_muy_bajo": precio_muy_bajo,
    "precio_algo_bajo": precio_algo_bajo,
    "deposito_antes_de_visitar": deposito_antes_de_visitar,
    "sin_direccion": sin_direccion,
    "solo_whatsapp": solo_whatsapp,
    "whatsapp_extranjero": whatsapp_extranjero,
    "descripcion_duplicada": descripcion_duplicada,
    "urgencia_presion": urgencia_presion,
    "sin_fotos_ni_visita": sin_fotos_ni_visita,
    "m2_inconsistente": m2_inconsistente,
    "sin_url_origen": sin_url_origen,
}
