"""Puntos de comunidad (spec 02, R4; tareas 6.2-6.3).

- OpenStreetMap vía `arraigo.fuentes.overpass.puntos_cercanos`, 800 m del centroide: mercados, parques y centros
  culturales, máximo 15 por categoría (los más cercanos).
- INEGI DENUE vía `arraigo.fuentes.inegi_denue.negocios_cercanos`, 500 m: solo un resumen de conteos por tipo de
  comercio de barrio, sin nombres ni direcciones de negocios. Sin `INEGI_TOKEN` se sigue solo con OSM (no es error).

Fallos: cada consulta se intenta como máximo `MAX_INTENTOS` (2) veces; si falla, el dato queda en `null` con su
motivo. Si una fuente falla en `MAX_FALLOS_SEGUIDOS` colonias seguidas, se deja de consultar en el resto de la corrida
(se anota el motivo) para no reintentar en bucle contra un servidor caído.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date

from arraigo.fuentes import inegi_denue, overpass
from arraigo.pipeline.enriquecer.geo import haversine_m
from arraigo.schemas.colonia import CategoriaComunidad, Colonia, ComercioLocal, Dato, PuntoComunidad

RADIO_OSM_M = 800
RADIO_DENUE_M = 500
MAX_POR_CATEGORIA = 15
PALABRAS_DENUE = ("mercado", "tianguis", "abarrotes", "fonda", "papeleria")
MAX_INTENTOS = 2
MAX_FALLOS_SEGUIDOS = 2

FUENTE_OSM = overpass.FUENTE
FUENTE_DENUE = inegi_denue.FUENTE
EXPLICACION = (
    "Mercados, parques y centros culturales a 800 m del centro aproximado de la colonia según OpenStreetMap, "
    "que tiene cobertura desigual: que no aparezca un lugar no significa que no exista."
)
EXPLICACION_DENUE = (
    "Conteo de comercios de barrio registrados en el DENUE del INEGI a 500 m del centro aproximado de la colonia."
)


# ---------- cálculos puros ----------


def puntos_desde_osm(
    crudos: Iterable[dict],
    lat: float,
    lng: float,
    max_por_categoria: int = MAX_POR_CATEGORIA,
) -> list[PuntoComunidad]:
    """Convierte la respuesta de `overpass.puntos_cercanos` en puntos ordenados por distancia.

    Descarta categorías ajenas (p. ej. `estacion_transporte`, que es de R2) y duplicados exactos.
    """
    categorias = {c.value for c in CategoriaComunidad}
    vistos: set[tuple] = set()
    por_categoria: dict[str, list[PuntoComunidad]] = {}
    for p in crudos:
        cat = p.get("categoria")
        if cat not in categorias or p.get("lat") is None or p.get("lng") is None:
            continue
        clave = (cat, p.get("nombre"), round(p["lat"], 6), round(p["lng"], 6))
        if clave in vistos:
            continue
        vistos.add(clave)
        por_categoria.setdefault(cat, []).append(
            PuntoComunidad(
                nombre=p.get("nombre"),
                tipo=cat,
                punto={"lat": p["lat"], "lng": p["lng"]},
                distancia_m=round(haversine_m(lat, lng, p["lat"], p["lng"])),
            )
        )
    salida: list[PuntoComunidad] = []
    for lista in por_categoria.values():
        salida.extend(sorted(lista, key=lambda x: x.distancia_m)[:max_por_categoria])
    return sorted(salida, key=lambda x: (x.distancia_m, x.tipo.value))


def resumir_denue(respuestas: dict[str, list[dict]], radio_m: int = RADIO_DENUE_M) -> ComercioLocal:
    """Cuenta negocios por palabra de búsqueda sin duplicar por `Id` (cada negocio cuenta en la primera palabra)."""
    vistos: set[str] = set()
    por_tipo: dict[str, int] = {}
    for palabra, negocios in respuestas.items():
        n = 0
        for negocio in negocios or []:
            ident = str(negocio.get("Id") or negocio.get("id") or "")
            if not ident or ident in vistos:
                continue
            vistos.add(ident)
            n += 1
        por_tipo[palabra] = n
    return ComercioLocal(radio_m=radio_m, total_negocios=len(vistos), por_tipo=por_tipo)


def _sin_token(texto: str) -> str:
    token = os.environ.get("INEGI_TOKEN")
    return texto.replace(token, "***") if token else texto


def con_reintentos(fn: Callable[[], object], intentos: int = MAX_INTENTOS) -> tuple[object | None, str | None]:
    """Llama `fn` hasta `intentos` veces. Regresa (resultado, None) o (None, motivo del último error)."""
    ultimo = ""
    for _ in range(intentos):
        try:
            return fn(), None
        except Exception as e:  # red, HTTP, JSON: todo se reporta igual
            ultimo = _sin_token(f"{type(e).__name__}: {e}")
    return None, f"falló {intentos} veces ({ultimo})"


# ---------- por colonia ----------


@dataclass
class ResultadoComunidad:
    puntos: Dato[list[PuntoComunidad]]
    comercio: Dato[ComercioLocal]
    motivos: list[str] = field(default_factory=list)
    fallo_osm: bool = False
    fallo_denue: bool = False


def enriquecer_colonia(
    lat: float,
    lng: float,
    *,
    hoy: date,
    consultar_osm: Callable[..., list[dict]] | None = overpass.puntos_cercanos,
    consultar_denue: Callable[..., list[dict]] | None = inegi_denue.negocios_cercanos,
) -> ResultadoComunidad:
    """Consulta OSM y DENUE para un centroide. `None` en un consultor = fuente omitida (sin token o caída)."""
    motivos: list[str] = []
    fallo_osm = fallo_denue = False

    puntos = Dato[list[PuntoComunidad]]()
    if consultar_osm is None:
        motivos.append("puntos_comunidad: OpenStreetMap omitido en esta corrida (falló en colonias anteriores)")
    else:
        crudos, error = con_reintentos(lambda: consultar_osm(lat, lng, RADIO_OSM_M))
        if error:
            fallo_osm = True
            motivos.append(f"puntos_comunidad: Overpass {error}")
        else:
            lista = puntos_desde_osm(crudos, lat, lng)
            puntos = Dato[list[PuntoComunidad]](
                valor=lista, fuente=FUENTE_OSM, fecha_dato=hoy, explicacion=EXPLICACION
            )
            if not lista:
                motivos.append("puntos_comunidad: 0 puntos en OpenStreetMap a 800 m (revisar cobertura)")

    comercio = Dato[ComercioLocal]()
    if consultar_denue is None:
        motivos.append("comercio_local: DENUE no consultado (falta INEGI_TOKEN o falló en colonias anteriores)")
    else:
        respuestas: dict[str, list[dict]] = {}
        for palabra in PALABRAS_DENUE:
            r, error = con_reintentos(lambda p=palabra: consultar_denue(lat, lng, RADIO_DENUE_M, p))
            if error:
                fallo_denue = True
                motivos.append(f"comercio_local: DENUE '{palabra}' {error}; se deja en null")
                break
            respuestas[palabra] = r if isinstance(r, list) else []
        if not fallo_denue:
            comercio = Dato[ComercioLocal](
                valor=resumir_denue(respuestas), fuente=FUENTE_DENUE, fecha_dato=hoy, explicacion=EXPLICACION_DENUE
            )

    if puntos.valor is not None and comercio.valor is None:
        puntos.fuente = f"{FUENTE_OSM} (sin DENUE)"
    return ResultadoComunidad(puntos, comercio, motivos, fallo_osm, fallo_denue)


# ---------- todas las colonias ----------


def enriquecer_comunidad(
    colonias: list[Colonia],
    *,
    hoy: date | None = None,
    consultar_osm: Callable[..., list[dict]] = overpass.puntos_cercanos,
    consultar_denue: Callable[..., list[dict]] = inegi_denue.negocios_cercanos,
    hay_token: bool | None = None,
    avisar: Callable[[str], None] = print,
) -> tuple[list[Colonia], dict[str, list[str]]]:
    """Llena `puntos_comunidad` y `comercio_local`. Regresa (colonias nuevas, {colonia: motivos})."""
    hoy = hoy or date.today()
    if hay_token is None:
        hay_token = bool(os.environ.get("INEGI_TOKEN"))
    if not hay_token:
        avisar("Aviso: no hay INEGI_TOKEN; se usa solo OpenStreetMap para puntos de comunidad.")

    osm: Callable | None = consultar_osm
    denue: Callable | None = consultar_denue if hay_token else None
    seguidos = {"osm": 0, "denue": 0}
    salida: list[Colonia] = []
    motivos: dict[str, list[str]] = {}

    for colonia in colonias:
        if colonia.centroide.valor is None:
            motivos[colonia.nombre] = ["puntos_comunidad y comercio_local: la colonia no tiene centroide"]
            salida.append(colonia)
            continue
        c = colonia.centroide.valor
        r = enriquecer_colonia(c.lat, c.lng, hoy=hoy, consultar_osm=osm, consultar_denue=denue)

        for fuente, fallo in (("osm", r.fallo_osm), ("denue", r.fallo_denue)):
            seguidos[fuente] = seguidos[fuente] + 1 if fallo else 0
        if osm is not None and seguidos["osm"] >= MAX_FALLOS_SEGUIDOS:
            osm = None
            avisar(f"Aviso: Overpass falló en {MAX_FALLOS_SEGUIDOS} colonias seguidas; se omite en el resto.")
        if denue is not None and seguidos["denue"] >= MAX_FALLOS_SEGUIDOS:
            denue = None
            avisar(f"Aviso: DENUE falló en {MAX_FALLOS_SEGUIDOS} colonias seguidas; se omite en el resto.")

        salida.append(colonia.model_copy(update={"puntos_comunidad": r.puntos, "comercio_local": r.comercio}))
        if r.motivos:
            motivos[colonia.nombre] = r.motivos
    return salida, motivos
