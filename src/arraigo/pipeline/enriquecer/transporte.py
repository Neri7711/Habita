"""Estaciones de transporte cercanas (spec 02, R2; tareas 3.2-3.4).

Fuentes:
- GTFS estático de la CDMX (Datos Abiertos CDMX, dataset `gtfs`, `data/raw/gtfs_semovi.zip`). El modo de cada parada
  se infiere uniendo `stop_times` -> `trips` -> `routes` y mapeando la agencia (tabla `MODO_POR_AGENCIA`; las rutas
  con `route_type = 11` son trolebús). Paradas de agencias fuera de los seis modos de R2 (RTP, corredores
  concesionados, Pumabús, Tren Interurbano, Suburbano) se descartan y se cuentan.
- Ecobici: feed GBFS público `station_information` (operado por Lyft).
- Respaldo si no hay GTFS: `overpass.puntos_cercanos` (categoría `estacion_transporte`). Ese cliente no regresa
  etiquetas OSM, así que el modo se infiere solo del nombre ("Metrobús ...", "Cablebús ..."); si no se puede inferir,
  la estación se omite (design.md: no se permite modo desconocido). Se marca en `fuente`.

Por centroide: paradas a ≤ 800 m (prefiltro por caja de coordenadas, luego haversine), fusión de duplicados (mismo
nombre normalizado y modo a < 50 m; GTFS trae una parada por andén o sentido) conservando la más cercana, y orden por
distancia. Una colonia sin estaciones queda con lista vacía (dato válido), distinta de `null` (dato no obtenido).
"""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from arraigo.fuentes import _http, overpass
from arraigo.pipeline.colonias import RAIZ, normalizar
from arraigo.pipeline.enriquecer.comunidad import con_reintentos
from arraigo.pipeline.enriquecer.geo import haversine_m
from arraigo.schemas.colonia import Colonia, Dato, Estacion, Modo

RUTA_GTFS = RAIZ / "data" / "raw" / "gtfs_semovi.zip"
URL_GTFS = (
    "https://datos.cdmx.gob.mx/dataset/75538d96-3ade-4bc5-ae7d-d85595e4522d/resource/"
    "32ed1b6b-41cd-49b3-b7f0-b57acb0eb819/download/32ed1b6b-41cd-49b3-b7f0-b57acb0eb819.zip"
)
FECHA_GTFS = date(2026, 9, 1)  # `metadata_modified` del dataset CKAN `gtfs` (el feed no trae feed_info.txt)
URL_ECOBICI = "https://gbfs.mex.lyftbikes.com/gbfs/es/station_information.json"

FUENTE_GTFS = "GTFS estático de la Ciudad de México (Datos Abiertos CDMX)"
FUENTE_ECOBICI = "Ecobici, feed GBFS station_information"
FUENTE_OSM = f"{overpass.FUENTE} (respaldo: GTFS no disponible; modo inferido por nombre)"

RADIO_M = 800
FUSION_M = 50
GRADOS_LAT_POR_M = 1 / 110_574
GRADOS_LNG_POR_M = 1 / 104_900  # en lat ~19.4

MODO_POR_AGENCIA: dict[str, Modo] = {
    "METRO": Modo.metro,
    "MB": Modo.metrobus,
    "TL": Modo.tren_ligero,
    "TROLE": Modo.trolebus,
    "CBB": Modo.cablebus,
}
ROUTE_TYPE_TROLEBUS = "11"
EXPLICACION = "Estaciones a 800 m o menos del centro aproximado de la colonia, en línea recta."


# ---------------- cálculos puros ----------------


def inferir_modos(
    stops: pd.DataFrame, stop_times: pd.DataFrame, trips: pd.DataFrame, routes: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    """Paradas con modo -> DataFrame (nombre, lat, lng, modo). También regresa cuántas paradas se descartaron."""
    r = routes[["route_id", "agency_id", "route_type"]].astype(str).copy()
    r["modo"] = r["agency_id"].map(MODO_POR_AGENCIA)
    r.loc[r["route_type"] == ROUTE_TYPE_TROLEBUS, "modo"] = Modo.trolebus
    pares = (
        stop_times[["trip_id", "stop_id"]].drop_duplicates()
        .merge(trips[["trip_id", "route_id"]], on="trip_id")
        .merge(r[["route_id", "modo"]], on="route_id")[["stop_id", "modo"]]
        .drop_duplicates()
    )
    con_modo = pares.dropna(subset=["modo"])
    descartadas = int(stops["stop_id"].nunique() - con_modo["stop_id"].nunique())
    salida = con_modo.merge(stops, on="stop_id").rename(
        columns={"stop_name": "nombre", "stop_lat": "lat", "stop_lon": "lng"}
    )
    salida["lat"] = pd.to_numeric(salida["lat"], errors="coerce")
    salida["lng"] = pd.to_numeric(salida["lng"], errors="coerce")
    return salida.dropna(subset=["lat", "lng"])[["nombre", "lat", "lng", "modo"]].reset_index(drop=True), descartadas


def estaciones_ecobici(station_information: dict) -> pd.DataFrame:
    filas = [
        {"nombre": s.get("name"), "lat": s.get("lat"), "lng": s.get("lon"), "modo": Modo.ecobici}
        for s in station_information.get("data", {}).get("stations", [])
        if s.get("lat") is not None and s.get("lon") is not None and s.get("name")
    ]
    return pd.DataFrame(filas, columns=["nombre", "lat", "lng", "modo"])


def modo_desde_nombre(nombre: str | None) -> Modo | None:
    """Respaldo OSM: modo solo si el nombre lo dice explícitamente."""
    n = normalizar(nombre or "")
    for clave, modo in (
        ("metrobus", Modo.metrobus),
        ("cablebus", Modo.cablebus),
        ("tren ligero", Modo.tren_ligero),
        ("trolebus", Modo.trolebus),
        ("ecobici", Modo.ecobici),
        ("metro", Modo.metro),
    ):
        if clave in n:
            return modo
    return None


def estaciones_cercanas(
    estaciones: pd.DataFrame, lat: float, lng: float, radio_m: int = RADIO_M, fusion_m: int = FUSION_M
) -> list[Estacion]:
    """Estaciones a ≤ `radio_m` del punto, sin duplicados (nombre y modo a < `fusion_m`), ordenadas por distancia."""
    if estaciones.empty:
        return []
    dlat, dlng = radio_m * GRADOS_LAT_POR_M * 1.05, radio_m * GRADOS_LNG_POR_M * 1.05
    caja = estaciones[estaciones["lat"].between(lat - dlat, lat + dlat) & estaciones["lng"].between(lng - dlng, lng + dlng)]
    candidatos = []
    for e in caja.itertuples(index=False):
        d = haversine_m(lat, lng, float(e.lat), float(e.lng))
        if d <= radio_m:
            candidatos.append((d, e))
    candidatos.sort(key=lambda x: x[0])

    elegidas: list[tuple[float, object]] = []
    for d, e in candidatos:  # el más cercano entra primero; un duplicado posterior se descarta
        duplicado = any(
            normalizar(e.nombre) == normalizar(o.nombre)
            and e.modo == o.modo
            and haversine_m(float(e.lat), float(e.lng), float(o.lat), float(o.lng)) < fusion_m
            for _, o in elegidas
        )
        if not duplicado:
            elegidas.append((d, e))
    return [
        Estacion(nombre=e.nombre, tipo=e.modo, punto={"lat": float(e.lat), "lng": float(e.lng)}, distancia_m=round(d))
        for d, e in elegidas
    ]


# ---------------- carga ----------------


def cargar_gtfs(ruta: Path = RUTA_GTFS) -> tuple[pd.DataFrame, int]:
    with zipfile.ZipFile(ruta) as z:
        def leer(nombre: str) -> pd.DataFrame:
            return pd.read_csv(io.BytesIO(z.read(nombre)), dtype=str, encoding="utf-8", encoding_errors="replace")

        return inferir_modos(leer("stops.txt"), leer("stop_times.txt"), leer("trips.txt"), leer("routes.txt"))


def obtener_ecobici(url: str = URL_ECOBICI) -> tuple[pd.DataFrame, date]:
    datos = _http.get_json(url, timeout=30)
    fecha = datetime.fromtimestamp(int(datos.get("last_updated", 0)), tz=timezone.utc).date()
    return estaciones_ecobici(datos), fecha


# ---------------- orquestación del campo ----------------


def enriquecer_transporte(
    colonias: list[Colonia],
    *,
    gtfs: pd.DataFrame | None = None,
    ecobici: tuple[pd.DataFrame, date] | None = None,
    consultar_osm: Callable[..., list[dict]] = overpass.puntos_cercanos,
    cargar_archivos: bool = True,
) -> tuple[list[Colonia], dict[str, list[str]]]:
    """Llena `estaciones_transporte_cercanas`. Regresa (colonias, {colonia: motivos})."""
    generales: list[str] = []
    if cargar_archivos and gtfs is None:
        try:
            gtfs, descartadas = cargar_gtfs()
            generales.append(f"GTFS: {descartadas} paradas descartadas por no ser de los seis modos (RTP, corredores, etc.)")
        except Exception as e:
            generales.append(f"GTFS no disponible ({type(e).__name__}: {e}); se usa respaldo OpenStreetMap")
    if cargar_archivos and ecobici is None:
        r, error = con_reintentos(obtener_ecobici)
        if error:
            generales.append(f"Ecobici GBFS {error}; la lista no incluye Ecobici")
        else:
            ecobici = r

    partes, fuentes, fechas = [], [], []
    if gtfs is not None:
        partes.append(gtfs)
        fuentes.append(FUENTE_GTFS)
        fechas.append(FECHA_GTFS)
    if ecobici is not None:
        partes.append(ecobici[0])
        fuentes.append(FUENTE_ECOBICI)
        fechas.append(ecobici[1])
    todas = pd.concat(partes, ignore_index=True) if partes else None

    salida, motivos = [], {}
    for c in colonias:
        m = list(generales)
        if c.centroide.valor is None:
            m.append("estaciones_transporte_cercanas: la colonia no tiene centroide")
            salida.append(c)
            motivos[c.nombre] = m
            continue
        lat, lng = c.centroide.valor.lat, c.centroide.valor.lng

        if gtfs is not None:
            lista = estaciones_cercanas(todas, lat, lng)
            dato = Dato[list[Estacion]](
                valor=lista, fuente="; ".join(fuentes), fecha_dato=min(fechas), explicacion=EXPLICACION
            )
        else:  # respaldo OSM (+ Ecobici si respondió)
            crudos, error = con_reintentos(lambda: consultar_osm(lat, lng, RADIO_M))
            if error:
                m.append(f"estaciones_transporte_cercanas: Overpass {error}")
                salida.append(c)
                motivos[c.nombre] = m
                continue
            filas = [
                {"nombre": p["nombre"], "lat": p["lat"], "lng": p["lng"], "modo": modo_desde_nombre(p.get("nombre"))}
                for p in crudos
                if p.get("categoria") == "estacion_transporte" and p.get("nombre")
            ]
            osm = pd.DataFrame(filas, columns=["nombre", "lat", "lng", "modo"]).dropna(subset=["modo"])
            omitidas = len(filas) - len(osm)
            if omitidas:
                m.append(f"estaciones_transporte_cercanas: {omitidas} estaciones OSM omitidas por modo no inferible")
            base = pd.concat([osm] + ([ecobici[0]] if ecobici else []), ignore_index=True)
            fuente = "; ".join([FUENTE_OSM] + ([FUENTE_ECOBICI] if ecobici else []))
            dato = Dato[list[Estacion]](
                valor=estaciones_cercanas(base, lat, lng), fuente=fuente, fecha_dato=date.today(),
                explicacion=EXPLICACION,
            )
        if not dato.valor:
            m.append("estaciones_transporte_cercanas: 0 estaciones a 800 m (lista vacía, dato válido)")
        salida.append(c.model_copy(update={"estaciones_transporte_cercanas": dato}))
        if m:
            motivos[c.nombre] = m
    return salida, motivos
