"""Herramientas del agente como funciones puras: (ctx, args) -> Envoltorio (R3-R8).

Los cálculos de la spec 03 (`arraigo.calculos.costo_real` y `precio_justo`) se usan a través de un adaptador:
si todavía no existen, las herramientas responden `{"aviso": "pendiente spec 03"}` en vez de reimplementarlos.
"""
from __future__ import annotations

import difflib
import importlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from arraigo.agente import explicaciones as ex
from arraigo.agente.contexto import ContextoAgente, normalizar_colonia
from arraigo.agente.envoltorio import (
    AVISO_HIPOTECA,
    AVISO_PENDIENTE_03,
    Envoltorio,
    Fuente,
    aviso_sin_dato,
    avisos_inmueble,
    deduplicar,
    deduplicar_fuentes,
    error,
    error_validacion,
    fuente_de_dato,
    inmueble_publico,
)
from arraigo.agente.ranking import (
    NOMBRE_CRITERIO,
    Candidato,
    Puntuado,
    filtros_duros,
    fraccion_peor,
    medida_comunidad,
    puntuar,
)
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble, Operacion
from arraigo.schemas.perfil import Perfil

log = logging.getLogger(__name__)

LIMITE_MAX = 10
MAX_ALTERNATIVAS = 3
EMPATE_ALTERNATIVAS = 5.0
MIN_ANUNCIOS_MEDIANA = 5
PENDIENTE = {"aviso": AVISO_PENDIENTE_03}

# ---------------------------------------------------------------------------------------------------------------
# Adaptador a la spec 03
# ---------------------------------------------------------------------------------------------------------------


def _funcion_calculos(nombre: str) -> Callable[..., Any] | None:
    """`arraigo.calculos.<nombre>` si ya existe; None si la spec 03 aún no lo publica."""
    try:
        modulo = importlib.import_module("arraigo.calculos")
    except ImportError:
        return None
    funcion = getattr(modulo, nombre, None)
    return funcion if callable(funcion) else None


def _a_dict(obj: Any) -> dict:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return obj
    raise TypeError(f"resultado inesperado de la spec 03: {type(obj).__name__}")


def _monto(componente: Any) -> int | None:
    if isinstance(componente, dict):
        return componente.get("monto_mxn")
    return componente if isinstance(componente, int) else None


@dataclass
class Costo:
    """Resumen de `arraigo.calculos.costo_real`, tolerante a nombres de campo."""

    total: int | None
    monetario: int | None
    vivienda: int | None
    transporte: int | None
    servicios: int | None
    tiempo: int | None
    minutos: int | None
    crudo: dict
    avisos: list[str] = field(default_factory=list)

    @classmethod
    def desde(cls, d: dict) -> Costo:
        traslado = d.get("traslado") or {}
        total = d.get("costo_real_mxn", d.get("total_mensual", d.get("total")))
        return cls(
            total=total,
            monetario=d.get("costo_monetario_mxn"),
            vivienda=_monto(d.get("vivienda")),
            transporte=_monto(d.get("transporte")),
            servicios=_monto(d.get("servicios")),
            tiempo=_monto(d.get("tiempo_valorizado")),
            minutos=traslado.get("minutos_ida", d.get("minutos_traslado")),
            crudo=d,
            avisos=list(d.get("avisos") or []),
        )

    def resumen(self) -> dict:
        return {"total_mensual_mxn": self.total, "costo_monetario_mxn": self.monetario,
                "vivienda_mxn": self.vivienda, "transporte_mxn": self.transporte, "servicios_mxn": self.servicios,
                "tiempo_valorizado_mxn": self.tiempo, "minutos_traslado": self.minutos}


def calcular_costo(inmueble: Inmueble, perfil: Perfil, colonia: Colonia | None) -> Costo | None:
    """None si la spec 03 no está; lanza la excepción de la spec 03 si el cálculo falla."""
    funcion = _funcion_calculos("costo_real")
    if funcion is None:
        return None
    return Costo.desde(_a_dict(funcion(inmueble, perfil, colonia)))


def calcular_precio_justo(inmueble: Inmueble, colonia: Colonia | None) -> dict | None:
    funcion = _funcion_calculos("precio_justo")
    if funcion is None:
        return None
    d = _a_dict(funcion(inmueble, colonia))
    banda = d.get("banda")
    if banda in (None, "no_evaluable"):
        banda = "sin_dato"
    return {
        "precio_m2": d.get("precio_m2"),
        "mediana_m2": d.get("mediana_m2", d.get("mediana")),
        "razon": d.get("razon"),
        "banda": banda,
        "motivo": d.get("motivo_no_evaluable", d.get("motivo")),
        "fuente_referencia": d.get("fuente_referencia", d.get("fuente")),
        "n_anuncios_mediana": d.get("n_anuncios_mediana"),
        "mediana_sintetica": "sint" in str(d.get("fuente_referencia") or "").lower(),
    }


def _avisos_calculo(avisos: list[str]) -> list[str]:
    """Avisos de la spec 03 sin el de sintético, que aquí se da con el texto fijo de R2.2."""
    return [a for a in avisos if not a.lower().startswith("este anuncio es sintético")]


def _pendiente(que: str) -> Envoltorio:
    return Envoltorio(
        datos=dict(PENDIENTE),
        explicacion=f"El cálculo de {que} todavía no está disponible ({AVISO_PENDIENTE_03}).",
        avisos=[AVISO_PENDIENTE_03],
    )


# ---------------------------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------------------------


def _perfil(perfil: Perfil | dict) -> Perfil:
    return perfil if isinstance(perfil, Perfil) else Perfil.model_validate(perfil)


def _buscar_inmueble(ctx: ContextoAgente, inmueble_id: str) -> tuple[Inmueble | None, Envoltorio | None]:
    """`inmueble_id` solo se usa como llave del diccionario."""
    inmueble = ctx.inmuebles.get(str(inmueble_id).strip())
    if inmueble:
        return inmueble, None
    parecidos = difflib.get_close_matches(str(inmueble_id), sorted(ctx.inmuebles), n=3, cutoff=0.5)
    texto = f"inmueble_id: no existe el anuncio '{inmueble_id}'."
    if parecidos:
        texto += f" ¿Quisiste decir {', '.join(parecidos)}?"
    return None, error(texto, {"ids_parecidos": parecidos})


def colonias_disponibles(ctx: ContextoAgente) -> list[str]:
    return sorted(ctx.nombres_colonia.values())


def resolver_colonia(ctx: ContextoAgente, texto: str) -> tuple[Colonia | None, list[str]]:
    """Coincidencia exacta normalizada; si no, prefijo o subcadena única. Devuelve (colonia, coincidencias)."""
    clave = normalizar_colonia(texto or "")
    if not clave:
        return None, []
    if clave in ctx.colonias:
        return ctx.colonias[clave], [ctx.nombres_colonia[clave]]
    for criterio in (lambda n: n.startswith(clave), lambda n: clave in n):
        hallados = [n for n in ctx.colonias if criterio(n)]
        if len(hallados) == 1:
            return ctx.colonias[hallados[0]], [ctx.nombres_colonia[hallados[0]]]
        if len(hallados) > 1:
            return None, sorted(ctx.nombres_colonia[n] for n in hallados)
    return None, []


def _presion(colonia: Colonia | None) -> float | None:
    return colonia.indicador_presion_gentrificacion.valor if colonia else None


def _dato_comunidad(colonia: Colonia | None) -> dict | None:
    if colonia is None:
        return None
    punto = ex.elegir_punto_integracion(colonia.puntos_comunidad.valor)
    if punto is None:
        return None
    return {"nombre": punto.nombre, "tipo": punto.tipo.value}


def _fuentes_colonia(colonia: Colonia | None, campos: tuple[str, ...]) -> list[Fuente]:
    if colonia is None:
        return []
    salida = []
    for campo in campos:
        f = fuente_de_dato(getattr(colonia, campo), colonia.nombre)
        if f:
            salida.append(f)
    return salida


def _fuentes_costo(costo: Costo) -> list[Fuente]:
    salida = []
    for clave in ("vivienda", "transporte", "servicios", "tiempo_valorizado"):
        comp = costo.crudo.get(clave)
        if isinstance(comp, dict) and comp.get("fuente") and comp.get("monto_mxn") is not None:
            salida.append(Fuente(descripcion=comp["fuente"], fecha_dato=comp.get("fecha_dato")))
    hip = costo.crudo.get("hipoteca")
    if isinstance(hip, dict) and hip.get("fuente_tasa"):
        salida.append(Fuente(descripcion=f"Tasa de referencia: {hip['fuente_tasa']}", fecha_dato=hip.get("fecha_tasa")))
    return salida


def _supuestos_costo(costo: Costo, perfil: Perfil) -> list[str]:
    supuestos = [f"Modo de transporte: {perfil.modo_transporte}"]
    traslado = costo.crudo.get("traslado")
    if isinstance(traslado, dict) and traslado.get("distancia_ruta_km") is not None:
        recta = traslado.get("distancia_recta_km")
        ruta = traslado["distancia_ruta_km"]
        if recta:
            supuestos.append(f"Factor de rodeo: {ruta / recta:.2f} ({recta:.1f} km en línea recta, {ruta:.1f} km de ruta)")
        if traslado.get("minutos_ida"):
            supuestos.append(f"Velocidad promedio: {ruta / (traslado['minutos_ida'] / 60):.1f} km/h "
                             f"({traslado['minutos_ida']} min de ida)")
    for clave in ("vivienda", "transporte", "servicios", "tiempo_valorizado"):
        comp = costo.crudo.get(clave)
        if isinstance(comp, dict):
            supuestos.extend(comp.get("supuestos") or [])
    hip = costo.crudo.get("hipoteca")
    if isinstance(hip, dict) and hip.get("tasa_anual_pct") is not None:
        supuestos.append(f"Tasa anual: {hip['tasa_anual_pct']:.2f}% a {hip.get('plazo_anios')} años, "
                         f"enganche {ex.mxn(hip.get('enganche_mxn') or 0)}")
    extra = costo.crudo.get("supuestos")
    if isinstance(extra, list):
        supuestos.extend(str(s) for s in extra)
    return deduplicar(supuestos)


# ---------------------------------------------------------------------------------------------------------------
# Ranking compartido por buscar_inmuebles y alternativas_equilibradas
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class Busqueda:
    puntuados: list[Puntuado]
    costos: dict[str, Costo]
    conteo: dict[str, int]
    excluidos_por_riesgo: int
    avisos: list[str]
    hay_calculos: bool


def rankear(ctx: ContextoAgente, perfil: Perfil, inmuebles: list[Inmueble]) -> Busqueda:
    """Filtros duros (R3.2-3.3), traslado (R3.4), riesgo alto (R3.5) y puntuación (R3.6-3.8)."""
    pasan, conteo = filtros_duros(sorted(inmuebles, key=lambda i: i.id), perfil)
    conteo["traslado"] = 0
    avisos: list[str] = []
    hay_calculos = _funcion_calculos("costo_real") is not None
    if not hay_calculos:
        avisos.append(f"{AVISO_PENDIENTE_03}: el costo real y el tiempo de traslado aún no se calculan; se ordenó "
                      "por precio publicado y no se filtró por tiempo de traslado.")

    candidatos: list[Candidato] = []
    costos: dict[str, Costo] = {}
    excluidos_riesgo = 0
    for inm in pasan:
        colonia = ctx.colonia_de(inm)
        costo = None
        if hay_calculos:
            try:
                costo = calcular_costo(inm, perfil, colonia)
            except Exception as exc:  # noqa: BLE001 - un anuncio que falla no tumba la búsqueda
                log.warning("costo_real falló para %s: %s", inm.id, exc)
                avisos.append(f"No se pudo calcular el costo real de {inm.id}; se usó su precio publicado.")
        if costo and costo.minutos is not None and costo.minutos > perfil.tiempo_max_traslado_min:
            conteo["traslado"] += 1
            continue
        riesgo = ctx.resultados_antifraude.get(inm.id)
        if riesgo and riesgo.nivel == "alto":
            excluidos_riesgo += 1
            continue
        if costo:
            costos[inm.id] = costo
        total = costo.total if costo and costo.total is not None else None
        candidatos.append(Candidato(inm, colonia, float(total if total is not None else inm.precio_mxn),
                                    float(costo.minutos) if costo and costo.minutos is not None else None))
    puntuados = puntuar(candidatos, list(perfil.prioridades), list(ctx.colonias.values()))
    return Busqueda(puntuados, costos, conteo, excluidos_riesgo, avisos, hay_calculos)


def _frase(p: Puntuado, criterio: str, todos: list[Puntuado], costo: Costo | None) -> str:
    c = p.candidato
    misma_op = [o.candidato for o in todos if o.candidato.inmueble.operacion == c.inmueble.operacion and o is not p]
    if criterio in p.faltantes:
        return ex.frase_criterio(NOMBRE_CRITERIO[criterio])
    if criterio == "precio":
        otros = [o.costo_mensual for o in misma_op if o.costo_mensual is not None]
        return ex.frase_criterio("precio", costo=c.costo_mensual,
                                 fraccion_peor=fraccion_peor(c.costo_mensual, otros, True),
                                 es_costo_real=bool(costo and costo.total is not None))
    if criterio == "traslado":
        otros = [o.minutos for o in misma_op if o.minutos is not None]
        return ex.frase_criterio("traslado", minutos=c.minutos, fraccion_peor=fraccion_peor(c.minutos, otros, True))
    if criterio == "espacio":
        otros = [o.inmueble.m2 for o in misma_op if o.inmueble.m2 is not None]
        return ex.frase_criterio("espacio", m2=c.inmueble.m2, fraccion_peor=fraccion_peor(c.inmueble.m2, otros, False))
    if criterio == "seguridad":
        return ex.frase_criterio("seguridad", valor_normalizado=p.criterios["seguridad"])
    comunidad = _dato_comunidad(c.colonia)
    total = medida_comunidad(c.colonia)
    ejemplo = None
    if comunidad and comunidad["nombre"]:
        ejemplo = comunidad["nombre"]
    return ex.frase_criterio("comunidad", puntos_comunidad=int(total or 0), ejemplo_comunidad=ejemplo)


def _resultado(ctx: ContextoAgente, lugar: int, p: Puntuado, todos: list[Puntuado], b: Busqueda) -> tuple[dict, list[str], list[Fuente]]:
    inm = p.candidato.inmueble
    colonia = p.candidato.colonia
    costo = b.costos.get(inm.id)
    avisos = avisos_inmueble(inm)
    for criterio in p.faltantes:
        avisos.append(aviso_sin_dato(NOMBRE_CRITERIO[criterio], f"{inm.id} ({inm.colonia})"))
    # precio justo: adaptador a spec 03
    try:
        pj = calcular_precio_justo(inm, colonia)
    except Exception as exc:  # noqa: BLE001
        log.warning("precio_justo falló para %s: %s", inm.id, exc)
        pj = {"banda": "sin_dato", "motivo": "no se pudo calcular"}
    precio_justo = dict(PENDIENTE) if pj is None else {"banda": pj["banda"]}
    riesgo = ctx.resultados_antifraude.get(inm.id)
    comunidad = _dato_comunidad(colonia)
    if comunidad is None and "comunidad" not in p.faltantes:
        avisos.append(aviso_sin_dato("lugares de comunidad", inm.colonia))
    # por_que: las 2 prioridades con más aporte que sí tienen dato (no se presume un valor neutro).
    con_dato = [k for k in p.desglose if k not in p.faltantes]
    orden = sorted(con_dato, key=lambda k: (-p.desglose[k], list(p.desglose).index(k)))
    frases = [_frase(p, k, todos, costo) for k in orden[:2]]
    fuentes = _fuentes_colonia(colonia, ("indice_delitos", "puntos_comunidad", "estaciones_transporte_cercanas"))
    if costo:
        fuentes += _fuentes_costo(costo)
        avisos += _avisos_calculo(costo.avisos)
    datos = {
        "inmueble": inmueble_publico(inm),
        "puntuacion": p.puntuacion,
        "desglose": p.desglose,
        "costo_real": costo.resumen() if costo else (dict(PENDIENTE) if not b.hay_calculos else None),
        "precio_justo": precio_justo,
        "score_riesgo": {"score": riesgo.score_riesgo, "nivel": riesgo.nivel} if riesgo else None,
        "comunidad": comunidad,
        "por_que": ex.por_que(lugar, frases),
        "avisos": deduplicar(avisos),
    }
    return datos, avisos, fuentes


def _filtro_mas_restrictivo(b: Busqueda) -> str | None:
    relajables = {k: v for k, v in b.conteo.items() if k != "operacion" and v > 0}
    if b.excluidos_por_riesgo:
        relajables["riesgo"] = b.excluidos_por_riesgo
    if not relajables:
        return None
    return max(relajables, key=lambda k: (relajables[k], k))


def _filtros_aplicados(perfil: Perfil) -> dict:
    return {
        "operacion": perfil.operacion_deseada,
        "presupuesto_max_mxn": perfil.presupuesto_max_mxn,
        "recamaras_min": perfil.recamaras_min,
        "mascotas": perfil.mascotas,
        "tiene_aval": perfil.tiene_aval,
        "tiempo_max_traslado_min": perfil.tiempo_max_traslado_min,
        "excluye_riesgo_alto": True,
    }


# ---------------------------------------------------------------------------------------------------------------
# Herramientas
# ---------------------------------------------------------------------------------------------------------------


def buscar_inmuebles(ctx: ContextoAgente, perfil: Perfil | dict, limite: int = 5) -> Envoltorio:
    """R3: opciones ordenadas según las prioridades del perfil."""
    try:
        perfil = _perfil(perfil)
    except ValidationError as exc:
        return error_validacion(exc, "perfil")
    if not isinstance(limite, int) or isinstance(limite, bool) or not 1 <= limite <= LIMITE_MAX:
        return error(f"Entrada inválida. limite: debe ser un número entero entre 1 y {LIMITE_MAX}")

    b = rankear(ctx, perfil, list(ctx.inmuebles.values()))
    base = {
        "total_candidatos": len(b.puntuados),
        "excluidos_por_riesgo": b.excluidos_por_riesgo,
        "descartados_por_filtro": b.conteo,
        "filtros_aplicados": _filtros_aplicados(perfil),
    }
    if not b.puntuados:
        filtro = _filtro_mas_restrictivo(b)
        sugerencia = ex.sugerencia_relajar(filtro)
        return Envoltorio(
            datos={"resultados": [], **base, "filtro_mas_restrictivo": filtro, "sugerencia": sugerencia},
            explicacion=f"Ningún anuncio cumple todo lo que pides. Lo que más opciones eliminó fue "
                        f"'{filtro or 'operación'}'; puedes {sugerencia}.",
            avisos=deduplicar(b.avisos),
        )

    resultados, avisos, fuentes = [], list(b.avisos), []
    for lugar, p in enumerate(b.puntuados[:limite], start=1):
        datos, av, fu = _resultado(ctx, lugar, p, b.puntuados, b)
        resultados.append(datos)
        avisos += av
        fuentes += fu
    if b.excluidos_por_riesgo:
        avisos.append(f"Se dejaron fuera {b.excluidos_por_riesgo} anuncio(s) con señales de riesgo altas.")
    primero = resultados[0]
    explicacion = (f"Encontramos {len(b.puntuados)} opciones que cumplen tus filtros; te mostramos las "
                   f"{len(resultados)} mejores según tus prioridades ({', '.join(perfil.prioridades)}). "
                   f"{primero['por_que']}")
    return Envoltorio(datos={"resultados": resultados, **base}, explicacion=explicacion,
                      fuentes=deduplicar_fuentes(fuentes), avisos=deduplicar(avisos))


def costo_real(ctx: ContextoAgente, inmueble_id: str, perfil: Perfil | dict) -> Envoltorio:
    """R4: desglose mensual del costo de vivir en el inmueble."""
    try:
        perfil = _perfil(perfil)
    except ValidationError as exc:
        return error_validacion(exc, "perfil")
    inm, err = _buscar_inmueble(ctx, inmueble_id)
    if err:
        return err
    if _funcion_calculos("costo_real") is None:
        return _pendiente("costo real")
    colonia = ctx.colonia_de(inm)
    try:
        costo = calcular_costo(inm, perfil, colonia)
    except Exception as exc:  # noqa: BLE001 - nunca sale una excepción al cliente (R2.8)
        log.warning("costo_real falló para %s: %s", inm.id, exc)
        return error(f"No se pudo calcular el costo real de {inm.id}: {exc}")
    es_venta = inm.operacion == Operacion.venta
    supuestos = _supuestos_costo(costo, perfil)
    avisos = avisos_inmueble(inm) + _avisos_calculo(costo.avisos)
    if es_venta:
        avisos.append(AVISO_HIPOTECA)
    for nombre, monto in (("vivienda", costo.vivienda), ("transporte", costo.transporte),
                          ("servicios", costo.servicios), ("tiempo de traslado valorizado", costo.tiempo)):
        if monto is None:
            avisos.append(aviso_sin_dato(nombre, inm.id))
    texto = ex.resumen_costo(costo.total, costo.vivienda, costo.transporte, costo.servicios, costo.tiempo, es_venta)
    if supuestos:
        texto += " Supuestos: " + "; ".join(supuestos) + "."
    datos = {"inmueble_id": inm.id, "operacion": inm.operacion.value, **costo.resumen(),
             "hipoteca": costo.crudo.get("hipoteca"), "supuestos": supuestos}
    return Envoltorio(datos=datos, explicacion=texto, fuentes=deduplicar_fuentes(_fuentes_costo(costo)),
                      avisos=deduplicar(avisos))


def precio_justo(ctx: ContextoAgente, inmueble_id: str) -> Envoltorio:
    """R5: precio por m² contra la mediana de la colonia."""
    inm, err = _buscar_inmueble(ctx, inmueble_id)
    if err:
        return err
    if _funcion_calculos("precio_justo") is None:
        return _pendiente("precio justo")
    colonia = ctx.colonia_de(inm)
    try:
        pj = calcular_precio_justo(inm, colonia)
    except Exception as exc:  # noqa: BLE001
        log.warning("precio_justo falló para %s: %s", inm.id, exc)
        return error(f"No se pudo calcular el precio justo de {inm.id}: {exc}")
    avisos = avisos_inmueble(inm)
    if pj["banda"] == "sin_dato":
        avisos.append(aviso_sin_dato("precio de referencia por m²", f"{inm.id} ({inm.colonia})"))
    n = pj.get("n_anuncios_mediana")
    if n is not None and n < MIN_ANUNCIOS_MEDIANA:
        avisos.append(f"La mediana de {inm.colonia} sale de pocos anuncios ({n}); tómala con cautela.")
    if pj.get("mediana_sintetica"):
        avisos.append("La mediana de referencia viene de anuncios sintéticos (de prueba).")
    fuentes = []
    if pj.get("fuente_referencia"):
        dato = (colonia.precio_m2_renta_mediana if inm.operacion == Operacion.renta
                else colonia.precio_m2_venta_mediana) if colonia else None
        fuentes.append(Fuente(descripcion=pj["fuente_referencia"], fecha_dato=dato.fecha_dato if dato else None))
    texto = ex.texto_precio_justo(pj["banda"], pj["precio_m2"], pj["mediana_m2"], inm.colonia,
                                  pj.get("fuente_referencia"), pj.get("motivo"))
    datos = {"inmueble_id": inm.id, **{k: pj[k] for k in ("precio_m2", "mediana_m2", "razon", "banda", "motivo")}}
    return Envoltorio(datos=datos, explicacion=texto, fuentes=fuentes, avisos=deduplicar(avisos))


def score_fraude(ctx: ContextoAgente, inmueble_id: str) -> Envoltorio:
    """R6: señales de riesgo del anuncio (spec 04). Nunca expone `es_fraude_prueba`."""
    inm, err = _buscar_inmueble(ctx, inmueble_id)
    if err:
        return err
    res = ctx.resultados_antifraude[inm.id]
    datos = res.model_dump(mode="json")
    datos.pop("es_fraude_prueba", None)
    texto = f"{res.resumen} {res.recomendacion}"
    if res.nivel == "bajo" and not res.senales and "no garantiza" not in texto:
        texto += " Esto no garantiza que el anuncio sea real."
    fuentes = []
    if res.fuente_referencia:
        mediana = ctx.antifraude.medianas_m2.get((normalizar_colonia(inm.colonia), inm.operacion))
        fuentes.append(Fuente(descripcion=res.fuente_referencia, fecha_dato=mediana.fecha_dato if mediana else None))
    return Envoltorio(datos=datos, explicacion=texto, fuentes=fuentes, avisos=deduplicar(avisos_inmueble(inm)))


CAMPOS_COLONIA = (
    ("precio_m2_renta_mediana", "mediana de precio por m² en renta"),
    ("precio_m2_venta_mediana", "mediana de precio por m² en venta"),
    ("indice_delitos", "índice de delitos"),
    ("estaciones_transporte_cercanas", "estaciones de transporte cercanas"),
    ("nivel_riesgo", "nivel de riesgo (sísmico e inundación)"),
    ("indicador_presion_gentrificacion", "presión de gentrificación"),
    ("puntos_comunidad", "puntos de comunidad"),
)


def _valor_json(valor: Any) -> Any:
    if isinstance(valor, BaseModel):
        return valor.model_dump(mode="json")
    if isinstance(valor, list):
        return [_valor_json(v) for v in valor]
    return valor


def info_colonia(ctx: ContextoAgente, colonia: str) -> Envoltorio:
    """R7: ficha de la colonia con procedencia por campo y sugerencia de integración."""
    col, coincidencias = resolver_colonia(ctx, colonia)
    if col is None:
        disponibles = colonias_disponibles(ctx)
        motivo = (f"'{colonia}' coincide con varias colonias ({', '.join(coincidencias)})" if coincidencias
                  else f"no encontramos la colonia '{colonia}'")
        return Envoltorio(
            datos={"colonias_disponibles": disponibles, "coincidencias": coincidencias},
            explicacion=f"Para darte la ficha necesito una sola colonia: {motivo}. "
                        f"Estas son las colonias disponibles: {', '.join(disponibles)}.",
        )
    campos: dict[str, Any] = {}
    avisos, fuentes = [], []
    for campo, nombre in CAMPOS_COLONIA:
        dato = getattr(col, campo)
        if dato.valor is None:
            campos[campo] = "sin dato"
            avisos.append(aviso_sin_dato(nombre, col.nombre))
            continue
        campos[campo] = {"valor": _valor_json(dato.valor), "fuente": dato.fuente,
                         "fecha_dato": dato.fecha_dato.isoformat() if dato.fecha_dato else None}
        if dato.explicacion:
            campos[campo]["explicacion"] = dato.explicacion
        fuentes.append(fuente_de_dato(dato, col.nombre))
    presion = _presion(col)
    partes = [f"{col.nombre} está en la alcaldía {col.alcaldia}.",
              ex.sugerencia_integracion(col.puntos_comunidad.valor, col.nombre)]
    if ex.es_presion_alta(presion):
        partes.append(ex.texto_presion(presion))
    if col.presion_gentrificacion_detalle.valor is not None:
        avisos.append("La presión de gentrificación es una estimación propia con datos públicos, no una medición oficial.")
    return Envoltorio(
        datos={"nombre": col.nombre, "alcaldia": col.alcaldia, "campos": campos},
        explicacion=" ".join(partes),
        fuentes=deduplicar_fuentes(f for f in fuentes if f),
        avisos=deduplicar(avisos),
    )


def _diferencia(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else round(a - b, 3)


def _ordenar_alternativas(mejores: list[Puntuado]) -> list[Puntuado]:
    """Por puntuación; si dos vecinas difieren ≤ 5 puntos, primero la de menor presión (R8.4)."""
    lista = sorted(mejores, key=lambda p: (-p.puntuacion, p.id))
    for i in range(1, len(lista)):
        j = i
        while j > 0:
            a, b = lista[j - 1], lista[j]
            pa, pb = _presion(a.candidato.colonia), _presion(b.candidato.colonia)
            if abs(a.puntuacion - b.puntuacion) <= EMPATE_ALTERNATIVAS and pb is not None and pa is not None and pb < pa:
                lista[j - 1], lista[j] = b, a
                j -= 1
            else:
                break
    return lista


def alternativas_equilibradas(ctx: ContextoAgente, perfil: Perfil | dict, colonia_origen: str | None = None) -> Envoltorio:
    """R8: hasta 3 colonias con menos presión de gentrificación que cumplen los filtros duros."""
    try:
        perfil = _perfil(perfil)
    except ValidationError as exc:
        return error_validacion(exc, "perfil")
    origen = None
    if colonia_origen:
        origen, coincidencias = resolver_colonia(ctx, colonia_origen)
        if origen is None:
            disponibles = colonias_disponibles(ctx)
            return error(f"colonia_origen: no encontramos una sola colonia para '{colonia_origen}'. "
                         f"Disponibles: {', '.join(disponibles)}.",
                         {"colonias_disponibles": disponibles, "coincidencias": coincidencias})

    avisos: list[str] = []
    presion_origen = _presion(origen)
    if origen and presion_origen is None:
        avisos.append(aviso_sin_dato("presión de gentrificación", origen.nombre))
    umbral = presion_origen if presion_origen is not None else ex.UMBRAL_PRESION_ALTA
    origen_alta = ex.es_presion_alta(presion_origen)

    candidatas, sin_presion = [], []
    for clave, col in ctx.colonias.items():
        if origen is not None and col is origen:
            continue
        p = _presion(col)
        if p is None:
            sin_presion.append(col.nombre)
        elif p < umbral:
            candidatas.append(clave)
    if sin_presion:
        avisos.append(f"No hay dato de presión de gentrificación para {', '.join(sorted(sin_presion))}; "
                      "esas colonias no se consideraron.")

    inmuebles = [i for i in ctx.inmuebles.values() if normalizar_colonia(i.colonia) in set(candidatas)]
    b = rankear(ctx, perfil, inmuebles)
    avisos += b.avisos
    mejores: dict[str, Puntuado] = {}
    for p in b.puntuados:  # ya vienen ordenados: el primero de cada colonia es el mejor
        mejores.setdefault(normalizar_colonia(p.candidato.inmueble.colonia), p)
    elegidas = _ordenar_alternativas(list(mejores.values()))[:MAX_ALTERNATIVAS]

    # Referencia en la colonia de origen: el mejor anuncio comparable con los mismos filtros.
    ref: Puntuado | None = None
    b_origen: Busqueda | None = None
    if origen is not None:
        b_origen = rankear(ctx, perfil, [i for i in ctx.inmuebles.values() if ctx.colonia_de(i) is origen])
        ref = b_origen.puntuados[0] if b_origen.puntuados else None

    alternativas, fuentes = [], []
    for lugar, p in enumerate(elegidas, start=1):
        datos, av, fu = _resultado(ctx, lugar, p, b.puntuados, b)
        col = p.candidato.colonia
        datos["colonia"] = col.nombre if col else p.candidato.inmueble.colonia
        datos["presion_gentrificacion"] = _presion(col)
        datos["comparacion_con_origen"] = _comparar(p, ref, origen, b, b_origen) if origen else None
        alternativas.append(datos)
        avisos += av
        fuentes += fu + _fuentes_colonia(col, ("indicador_presion_gentrificacion",))
    if origen:
        fuentes += _fuentes_colonia(origen, ("indicador_presion_gentrificacion", "indice_delitos"))

    nombre_origen = origen.nombre if origen else None
    if not alternativas:
        texto = ("No encontramos alternativas con menos presión de gentrificación que cumplan tus filtros "
                 "(presupuesto, operación, recámaras, traslado y riesgo). No te mostramos opciones que no los cumplan.")
    else:
        nombres = ", ".join(a["colonia"] for a in alternativas)
        if origen_alta:
            texto = ex.texto_alternativa(nombre_origen, alternativas[0]["colonia"])
        elif origen and presion_origen is not None:
            texto = (f"{nombre_origen} no es una colonia de alta presión de gentrificación; aun así, estas opciones "
                     f"tienen menos presión. {ex.texto_alternativa(None, alternativas[0]['colonia'])}")
        else:
            texto = ex.texto_alternativa(None, alternativas[0]["colonia"])
        texto += f" Opciones: {nombres}."
    return Envoltorio(
        datos={"colonia_origen": nombre_origen, "presion_origen": presion_origen, "umbral_presion": umbral,
               "alternativas": alternativas, "excluidos_por_riesgo": b.excluidos_por_riesgo},
        explicacion=texto,
        fuentes=deduplicar_fuentes(fuentes),
        avisos=deduplicar(avisos),
    )


def _mediana_op(col: Colonia | None, op: Operacion) -> float | None:
    if col is None:
        return None
    return (col.precio_m2_renta_mediana if op == Operacion.renta else col.precio_m2_venta_mediana).valor


def _comparar(p: Puntuado, ref: Puntuado | None, origen: Colonia, b: Busqueda, b_origen: Busqueda | None) -> dict:
    """Diferencias alternativa − origen (negativo = la alternativa tiene menos)."""
    col = p.candidato.colonia
    comp = {
        "diferencia_indice_delitos": _diferencia(col.indice_delitos.valor if col else None, origen.indice_delitos.valor),
        "diferencia_presion": _diferencia(_presion(col), _presion(origen)),
    }
    if ref is not None:
        costo_alt = b.costos.get(p.id)
        costo_ref = b_origen.costos.get(ref.id) if b_origen else None
        comp["referencia_origen"] = ref.id
        comp["diferencia_costo_mensual_mxn"] = _diferencia(
            costo_alt.total if costo_alt else p.candidato.costo_mensual,
            costo_ref.total if costo_ref else ref.candidato.costo_mensual)
        comp["diferencia_minutos_traslado"] = _diferencia(p.candidato.minutos, ref.candidato.minutos)
    else:
        op = p.candidato.inmueble.operacion
        comp["referencia_origen"] = None
        comp["diferencia_mediana_m2"] = _diferencia(_mediana_op(col, op), _mediana_op(origen, op))
        comp["nota"] = f"{origen.nombre} no tiene anuncios que cumplan tus filtros; se comparan medianas de la colonia."
    return comp
