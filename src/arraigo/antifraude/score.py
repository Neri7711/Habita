"""Score 0-100 explicable. Interfaz pública para la herramienta `score_fraude` (spec 05)."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import median

from arraigo.antifraude.modelos import (
    ConfigReglas,
    ContextoAntifraude,
    NoEvaluable,
    ResultadoAntifraude,
    Senal,
    cargar_config,
)
from arraigo.antifraude.duplicados import IndiceDuplicados
from arraigo.antifraude.reglas import REGISTRO, TITULOS, mediana_de
from arraigo.antifraude.texto import normalizar
from arraigo.schemas.colonia import Colonia, Dato
from arraigo.schemas.inmueble import Inmueble, Operacion

RECOMENDACIONES = {
    "alto": "No pagues nada ni compartas documentos. Pide ver el lugar en persona y conocer a quien lo renta.",
    "medio": "Confirma la dirección y visita el lugar antes de pagar cualquier cosa.",
    "bajo": "Aun así, visita el lugar y no pagues antes de firmar.",
}


def nivel_de_score(score: int, config: ConfigReglas) -> str:
    if score >= config.niveles["alto"]:
        return "alto"
    if score >= config.niveles["medio"]:
        return "medio"
    return "bajo"


def construir_contexto(
    inmuebles: list[Inmueble], colonias: list[Colonia], config: ConfigReglas | None = None
) -> ContextoAntifraude:
    """Medianas por colonia y operación + índice de descripciones.

    Se usa la mediana de `colonias.json` (la misma de la spec 03). Si la colonia aún no la trae, se usa
    como respaldo la mediana de los anuncios del propio dataset (mínimo `min_anuncios_mediana` con m2).
    """
    config = config or cargar_config()
    medianas: dict[tuple[str, Operacion], Dato[float]] = {}
    for c in colonias:
        for op, dato in ((Operacion.renta, c.precio_m2_renta_mediana), (Operacion.venta, c.precio_m2_venta_mediana)):
            if dato.valor is not None:
                medianas[(normalizar(c.nombre), op)] = dato

    grupos: dict[tuple[str, Operacion], list[Inmueble]] = defaultdict(list)
    for i in inmuebles:
        if i.m2:
            grupos[(normalizar(i.colonia), i.operacion)].append(i)
    for clave, items in grupos.items():
        if clave in medianas or len(items) < config.min_anuncios_mediana:
            continue
        fechas: list[date] = [i.fecha_captura for i in items]
        n_sinteticos = sum(i.fuente == "sintetico" for i in items)
        if n_sinteticos:
            # La etiqueta debe decir "sintéticos": calculos/banda_precio.py busca "sint" para avisar al usuario.
            fuente = (f"mediana de anuncios sintéticos de ejemplo, no es dato de mercado "
                      f"(n={len(items)}, {len(items) - n_sinteticos} reales)")
        else:
            fuente = f"mediana de anuncios capturados (n={len(items)})"
        medianas[clave] = Dato[float](
            valor=float(median(i.precio_mxn / i.m2 for i in items)),
            fuente=fuente,
            fecha_dato=max(fechas),
        )

    indice = IndiceDuplicados()
    for i in inmuebles:
        indice.agregar(i.id, i.colonia, i.precio_mxn, i.descripcion)
    return ContextoAntifraude(medianas_m2=medianas, indice_duplicados=indice, config=config)


def _resumen(senales: list[Senal], es_sintetico: bool) -> str:
    if not senales:
        texto = "No encontramos señales de riesgo en lo que podemos revisar. Eso no garantiza que el anuncio sea real."
    else:
        n = len(senales)
        plural = "señal de riesgo" if n == 1 else "señales de riesgo"
        texto = f"Encontramos {n} {plural}. La más importante: {TITULOS[senales[0].regla]}."
    if es_sintetico:
        texto += " Este anuncio es de ejemplo (sintético)."
    return texto


def evaluar_anuncio(inmueble: Inmueble, contexto: ContextoAntifraude) -> ResultadoAntifraude:
    """Evalúa un anuncio con las reglas del registro. No lee `es_fraude_prueba`."""
    senales: list[Senal] = []
    no_evaluables: list[str] = []
    for regla, funcion in REGISTRO.items():
        r = funcion(inmueble, contexto)
        if isinstance(r, Senal):
            senales.append(r)
        elif isinstance(r, NoEvaluable):
            no_evaluables.append(f"{r.regla}: {r.motivo}")
    # Orden estable: más puntos primero.
    senales.sort(key=lambda s: -s.puntos)

    score = min(100, sum(s.puntos for s in senales))
    nivel = nivel_de_score(score, contexto.config)
    es_sintetico = inmueble.fuente == "sintetico"

    fuente_ref = None
    mediana = mediana_de(inmueble, contexto)
    if mediana is not None:
        fuente_ref = (
            f"Mediana de precio por m² ({mediana.fuente}), {inmueble.colonia}, {mediana.fecha_dato.isoformat()}"
        )
    return ResultadoAntifraude(
        id=inmueble.id,
        score_riesgo=score,
        nivel=nivel,
        senales=senales,
        no_evaluables=no_evaluables,
        resumen=_resumen(senales, es_sintetico),
        recomendacion=RECOMENDACIONES[nivel],
        fuente_referencia=fuente_ref,
        es_sintetico=es_sintetico,
    )


def evaluar_anuncio_nuevo(
    descripcion: str,
    precio_mxn: int,
    colonia: str,
    contexto: ContextoAntifraude,
    operacion: Operacion | str = Operacion.renta,
    m2: float | None = None,
    alcaldia: str = "CDMX",
    url_origen: str | None = None,
    id: str = "nuevo",
) -> ResultadoAntifraude:
    """Evalúa un anuncio pegado por el usuario con las mismas reglas (fuente: captura manual)."""
    inmueble = Inmueble(
        id=id, operacion=Operacion(operacion), precio_mxn=precio_mxn, colonia=colonia, alcaldia=alcaldia,
        m2=m2, recamaras=0, banos=1, descripcion=descripcion, fuente="captura_manual",
        fecha_captura=date.today(), url_origen=url_origen,
    )
    return evaluar_anuncio(inmueble, contexto)
