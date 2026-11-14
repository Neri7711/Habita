"""Servidor MCP de Arraigo (spec 05): expone las herramientas de `arraigo.agente.herramientas` a Kiro.

Capa delgada: valida argumentos, llama a la función pura y devuelve el Envoltorio como dict. Cero lógica de negocio.
Arranque (lo hace Kiro como proceso hijo por stdio): `uv run python -m arraigo.agente.mcp_server`.
`stdout` queda reservado al protocolo MCP; los registros van a `stderr` (R1.6).
"""
from __future__ import annotations

import copy
import functools
import logging
import sys
from typing import Annotated, Any, Callable

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field, WithJsonSchema

from arraigo.agente import herramientas
from arraigo.agente.contexto import ContextoAgente, ErrorDatos, cargar_contexto
from arraigo.agente.envoltorio import Envoltorio, error
from arraigo.schemas.perfil import Perfil

log = logging.getLogger("arraigo.mcp")

INSTRUCCIONES = """Eres el asesor de vivienda de Arraigo para personas que se mudan a la CDMX.
1. Solo recomiendas. No contactas caseros, no pagas, no firmas y no das asesoría legal ni financiera.
2. Para recomendar, usa las herramientas; no inventes precios, inmuebles ni datos de colonias.
3. Cita la fuente y la fecha de cada dato importante (campo `fuentes`). Si falta un dato, dilo.
4. Muestra siempre los avisos del campo `avisos` (anuncio sintético, ubicación aproximada, estimación hipotecaria).
5. Habla de "señales de riesgo"; nunca acuses a nadie de estafa.
6. Para cada opción, muestra costo real, precio justo, nivel de confianza y un dato de comunidad.
7. Si la colonia tiene alta presión de gentrificación, ofrece `alternativas_equilibradas`.
8. Tono claro y cercano, sin jerga inmobiliaria."""

SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


def _esquema_en_linea(modelo: type) -> dict:
    """JSON Schema del modelo con los `$defs` resueltos, para incrustarlo en el esquema de la herramienta."""
    esquema = modelo.model_json_schema()
    defs = esquema.pop("$defs", {})

    def resolver(nodo: Any) -> Any:
        if isinstance(nodo, dict):
            if "$ref" in nodo:
                return resolver(copy.deepcopy(defs[nodo["$ref"].split("/")[-1]]))
            return {k: resolver(v) for k, v in nodo.items()}
        if isinstance(nodo, list):
            return [resolver(v) for v in nodo]
        return nodo

    return resolver(esquema)


# Se recibe como dict para validar nosotros y responder el error en español (R2.8),
# pero se anuncia a Kiro con el esquema completo de `Perfil`.
PerfilArg = Annotated[dict[str, Any], WithJsonSchema(_esquema_en_linea(Perfil)),
                      Field(description="Perfil del usuario (esquema Perfil de la spec 01).")]

# ---------------------------------------------------------------------------------------------------------------
# Contexto: se carga una sola vez; si faltan datos, el servidor arranca igual y cada herramienta lo explica (R1.4)
# ---------------------------------------------------------------------------------------------------------------

_estado: dict[str, Any] = {"ctx": None, "error": None}


def configurar_contexto(ctx: ContextoAgente | None) -> None:
    """Inyecta un contexto ya armado (pruebas) o lo reinicia con None."""
    _estado["ctx"], _estado["error"] = ctx, None


def obtener_contexto() -> ContextoAgente:
    if _estado["ctx"] is None and _estado["error"] is None:
        try:
            _estado["ctx"] = cargar_contexto()
            log.info("Datos cargados: %d anuncios, %d colonias", len(_estado["ctx"].inmuebles),
                     len(_estado["ctx"].colonias))
        except ErrorDatos as exc:
            _estado["error"] = str(exc)
            log.error("No se pudieron cargar los datos: %s", exc)
    if _estado["ctx"] is None:
        raise ErrorDatos(_estado["error"])
    return _estado["ctx"]


def _responder(funcion: Callable[..., Envoltorio]) -> Callable[..., dict]:
    """Ninguna excepción sale al cliente: todo termina en un Envoltorio (R2.8, R1.4)."""

    @functools.wraps(funcion)
    def envuelta(*args: Any, **kwargs: Any) -> dict:
        try:
            env = funcion(*args, **kwargs)
        except ErrorDatos as exc:
            env = error(str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("Error inesperado en %s", funcion.__name__)
            env = error(f"Error interno al ejecutar {funcion.__name__}: {type(exc).__name__}. Intenta de nuevo.")
        return env.model_dump(mode="json")

    return envuelta


mcp = FastMCP("arraigo", instructions=INSTRUCCIONES)

# ---------------------------------------------------------------------------------------------------------------
# Herramientas (solo lectura). Los docstrings son lo que Kiro lee para decidir cuál usar.
# ---------------------------------------------------------------------------------------------------------------


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def buscar_inmuebles(
    perfil: PerfilArg,
    limite: Annotated[int, Field(description="Cuántas opciones devolver (1 a 10).")] = 5,
) -> Envoltorio:
    """Busca anuncios de renta o compra que cumplen el perfil y los ordena según sus prioridades.

    Úsala cuando el usuario quiera opciones de vivienda. Filtra por operación, presupuesto, recámaras,
    mascotas, aval, tiempo de traslado y excluye anuncios con señales de riesgo altas. Cada resultado trae
    puntuación 0-100, aporte de cada prioridad, costo real resumido, banda de precio justo, nivel de riesgo,
    un lugar de comunidad y `por_que`. Si no hay resultados, dice qué filtro conviene relajar.
    """
    return herramientas.buscar_inmuebles(obtener_contexto(), perfil, limite)


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def costo_real(
    inmueble_id: Annotated[str, Field(description="id del anuncio, por ejemplo 'sint-0001'.")],
    perfil: PerfilArg,
) -> Envoltorio:
    """Calcula cuánto cuesta al mes vivir en un anuncio: renta o mensualidad de compra, transporte,
    servicios y el valor del tiempo de traslado, con los supuestos usados y sus fuentes.

    Úsala cuando el usuario pregunte cuánto le costaría realmente un anuncio. En compra incluye la mensualidad
    estimada con la tasa de referencia y el enganche del perfil (no es asesoría hipotecaria).
    """
    return herramientas.costo_real(obtener_contexto(), inmueble_id, perfil)


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def precio_justo(
    inmueble_id: Annotated[str, Field(description="id del anuncio, por ejemplo 'sint-0001'.")],
) -> Envoltorio:
    """Compara el precio por m² del anuncio con la mediana de su colonia y lo clasifica como
    `justo`, `caro`, `sospechosamente_barato` o `sin_dato`.

    Úsala cuando el usuario pregunte si un precio es razonable. Si sale `sospechosamente_barato`,
    revisa también `score_fraude`.
    """
    return herramientas.precio_justo(obtener_contexto(), inmueble_id)


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def score_fraude(
    inmueble_id: Annotated[str, Field(description="id del anuncio, por ejemplo 'sint-0001'.")],
) -> Envoltorio:
    """Revisa las señales de riesgo de un anuncio (depósito antes de visitar, precio muy bajo, sin dirección,
    solo WhatsApp, descripción duplicada, etc.) y da un score 0-100 con nivel bajo, medio o alto,
    explicado en palabras simples y con una recomendación.

    Úsala cuando el usuario dude si un anuncio es confiable. Un nivel bajo no garantiza que el anuncio sea real.
    """
    return herramientas.score_fraude(obtener_contexto(), inmueble_id)


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def info_colonia(
    colonia: Annotated[str, Field(description="Nombre de la colonia; acepta minúsculas y sin acentos.")],
) -> Envoltorio:
    """Ficha de una colonia: alcaldía, medianas de precio por m², índice de delitos, estaciones cercanas,
    riesgo sísmico y de inundación, presión de gentrificación y lugares de comunidad, cada dato con su fuente
    y fecha. Incluye una sugerencia concreta para integrarse a la colonia.

    Úsala cuando el usuario pregunte por una colonia o si le conviene vivir ahí. Si el nombre es ambiguo,
    devuelve la lista de colonias disponibles.
    """
    return herramientas.info_colonia(obtener_contexto(), colonia)


@mcp.tool(annotations=SOLO_LECTURA)
@_responder
def alternativas_equilibradas(
    perfil: PerfilArg,
    colonia_origen: Annotated[str | None, Field(description="Colonia que el usuario tenía en mente (opcional).")] = None,
) -> Envoltorio:
    """Propone hasta 3 colonias con menos presión de gentrificación que la colonia de origen y que cumplen
    el perfil, comparando costo real, minutos de traslado, índice de delitos y presión.

    Úsala cuando el usuario quiera vivir en una colonia de alta presión (por ejemplo, Roma Norte) o pida
    opciones parecidas en otras zonas. No rellena con colonias que no cumplen los filtros.
    """
    return herramientas.alternativas_equilibradas(obtener_contexto(), perfil, colonia_origen)


HERRAMIENTAS = ("buscar_inmuebles", "costo_real", "precio_justo", "score_fraude", "info_colonia",
                "alternativas_equilibradas")


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    try:
        obtener_contexto()  # carga única al iniciar; si falla, el servidor sigue y cada herramienta lo explica
    except ErrorDatos:
        pass
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
