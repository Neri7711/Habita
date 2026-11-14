"""Plantillas de texto en español sencillo (R3.9, R7.5, R7.6, R8.5).

Cada cifra llega como parámetro; ninguna está escrita a mano en el texto.
"""
from __future__ import annotations

from arraigo.schemas.colonia import CategoriaComunidad, PuntoComunidad

UMBRAL_PRESION_ALTA = 0.66
ORDEN_INTEGRACION = (CategoriaComunidad.mercado, CategoriaComunidad.parque, CategoriaComunidad.centro_cultural)
NOMBRE_TIPO = {
    CategoriaComunidad.mercado: "mercado",
    CategoriaComunidad.parque: "parque",
    CategoriaComunidad.centro_cultural: "centro cultural",
}


def mxn(monto: float | int) -> str:
    return f"${round(monto):,}"


def frase_criterio(
    criterio: str,
    *,
    costo: float | None = None,
    minutos: float | None = None,
    m2: float | None = None,
    puntos_comunidad: int | None = None,
    ejemplo_comunidad: str | None = None,
    valor_normalizado: float | None = None,
    fraccion_peor: float | None = None,
    es_costo_real: bool = True,
) -> str:
    """Frase de un criterio. Solo compara ('menos que la mayoría') si `fraccion_peor` > 0.5."""
    mayoria = fraccion_peor is not None and fraccion_peor > 0.5
    if criterio == "precio" and costo is not None:
        base = (f"cuesta en total {mxn(costo)} al mes con transporte y tiempo" if es_costo_real
                else f"cuesta {mxn(costo)} de precio publicado")
        return f"{base}, menos que la mayoría de las opciones" if mayoria else base
    if criterio == "traslado" and minutos is not None:
        base = f"llegas al trabajo en unos {round(minutos)} minutos"
        return f"{base}, menos que la mayoría de las opciones" if mayoria else base
    if criterio == "seguridad" and valor_normalizado is not None:
        if valor_normalizado >= 0.5:
            return "la colonia tiene pocos reportes de delitos comparada con las demás"
        return "la colonia tiene más reportes de delitos que otras, aunque compensa en lo demás"
    if criterio == "comunidad" and puntos_comunidad is not None:
        if ejemplo_comunidad:
            return f"tiene {puntos_comunidad} lugares de comunidad y transporte cerca, como {ejemplo_comunidad}"
        return f"tiene {puntos_comunidad} lugares de comunidad y transporte cerca"
    if criterio == "espacio" and m2 is not None:
        base = f"tiene {m2:g} m²"
        return f"{base}, más que la mayoría de las opciones" if mayoria else base
    return f"no tenemos dato de {criterio}, así que en ese punto quedó en un valor medio"


def por_que(lugar: int, frases: list[str]) -> str:
    """'Quedó en el lugar {n} porque {p1} y {p2}, que son tus prioridades principales.'"""
    frases = [f for f in frases if f][:2]
    if not frases:
        return f"Quedó en el lugar {lugar}."
    if len(frases) == 1:
        return f"Quedó en el lugar {lugar} porque {frases[0]}, que es tu prioridad principal."
    return f"Quedó en el lugar {lugar} porque {frases[0]} y {frases[1]}, que son tus prioridades principales."


def resumen_costo(
    total: int | None,
    vivienda: int | None,
    transporte: int | None,
    servicios: int | None,
    tiempo: int | None,
    es_venta: bool,
) -> str:
    concepto = "la mensualidad estimada" if es_venta else "la renta"
    partes = []
    if vivienda is not None:
        partes.append(f"{concepto} ({mxn(vivienda)})")
    if transporte is not None:
        partes.append(f"transporte ({mxn(transporte)})")
    if servicios is not None:
        partes.append(f"servicios ({mxn(servicios)})")
    if tiempo is not None:
        partes.append(f"el valor de tu tiempo de traslado ({mxn(tiempo)})")
    if total is None:
        return "No pudimos calcular el costo total; " + (
            "estos son los componentes que sí se calcularon: " + ", ".join(partes) + "." if partes
            else "no hay componentes calculados.")
    detalle = ", ".join(partes[:-1]) + f" y {partes[-1]}" if len(partes) > 1 else "".join(partes)
    return f"Vivir aquí te costaría unos {mxn(total)} al mes: {detalle}."


def elegir_punto_integracion(puntos: list[PuntoComunidad] | None) -> PuntoComunidad | None:
    """Primero un mercado, luego un parque, luego un centro cultural; con nombre si hay, y el más cercano."""
    if not puntos:
        return None
    for tipo in ORDEN_INTEGRACION:
        del_tipo = [p for p in puntos if p.tipo == tipo]
        if not del_tipo:
            continue
        del_tipo.sort(key=lambda p: (p.nombre is None, p.distancia_m is None, p.distancia_m or 0.0, p.nombre or ""))
        return del_tipo[0]
    return None


def nombre_punto(punto: PuntoComunidad) -> str:
    tipo = NOMBRE_TIPO[punto.tipo]
    return f"el {tipo} {punto.nombre}" if punto.nombre else f"un {tipo} cercano"


def sugerencia_integracion(puntos: list[PuntoComunidad] | None, colonia: str) -> str:
    punto = elegir_punto_integracion(puntos)
    if punto is None:
        return f"No tenemos datos de lugares de comunidad (mercados, parques o centros culturales) para {colonia}."
    return f"Para conocer la colonia, puedes empezar por {nombre_punto(punto)}."


def es_presion_alta(valor: float | None) -> bool:
    return valor is not None and valor >= UMBRAL_PRESION_ALTA


def texto_presion(valor: float | None) -> str:
    if not es_presion_alta(valor):
        return ""
    return ("Esta colonia está bajo fuerte presión de gentrificación. "
            "Puedes ver opciones más equilibradas con `alternativas_equilibradas`.")


def texto_alternativa(origen: str | None, alternativa: str) -> str:
    """Texto fijo y verificable; no atribuye causas al usuario (R8.5)."""
    if origen:
        return (f"{origen} tiene una presión alta: los precios y la demanda han subido y eso puede desplazar a "
                f"vecinos de toda la vida. {alternativa} cumple lo que buscas con menos presión.")
    return f"{alternativa} cumple lo que buscas y está bajo menos presión de gentrificación."


def texto_precio_justo(
    banda: str,
    precio_m2: float | None,
    mediana_m2: float | None,
    colonia: str,
    origen_mediana: str | None,
    motivo: str | None = None,
) -> str:
    if banda == "sin_dato" or precio_m2 is None or mediana_m2 is None:
        return f"No podemos decir si el precio es justo: {motivo or 'falta el dato de m² o la mediana'}."
    diff = (precio_m2 / mediana_m2 - 1) * 100
    comparacion = (f"El anuncio cuesta {mxn(precio_m2)} por m² y la mediana de {colonia} es {mxn(mediana_m2)} por m² "
                   f"({abs(diff):.0f}% {'más' if diff >= 0 else 'menos'}).")
    if banda == "justo":
        texto = f"El precio está dentro de lo normal para la colonia. {comparacion}"
    elif banda == "caro":
        texto = f"El precio está por encima de lo normal para la colonia. {comparacion}"
    else:
        texto = (f"El precio está muy por debajo de lo normal para la colonia. {comparacion} "
                 "Antes de decidir, revisa sus señales de riesgo con `score_fraude`.")
    if origen_mediana:
        texto += f" Referencia: {origen_mediana}."
    return texto


def sugerencia_relajar(filtro: str | None) -> str:
    textos = {
        "presupuesto": "subir un poco el presupuesto máximo",
        "traslado": "aceptar un tiempo de traslado mayor",
        "aval": "considerar anuncios que piden aval (o conseguir uno)",
        "recamaras": "bajar el mínimo de recámaras",
        "mascotas": "revisar anuncios que no dicen si aceptan mascotas",
        "riesgo": "ninguno: los que quedaron tienen señales de riesgo altas y no te los recomendamos",
        "operacion": "cambiar el tipo de operación (renta o compra)",
    }
    return textos.get(filtro or "", "revisar tus filtros")
