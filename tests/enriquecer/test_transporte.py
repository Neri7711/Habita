"""Transporte con datos simulados (sin red ni archivos)."""

from datetime import date

import pandas as pd

from arraigo.pipeline.enriquecer import transporte as tr
from arraigo.schemas.colonia import Colonia, Modo

LAT, LNG = 19.4195, -99.1620
M_LAT = 1 / 110_574  # grados por metro de latitud


def colonia(nombre="Roma Norte", con_centroide=True):
    c = {"nombre": nombre, "alcaldia": "Cuauhtémoc"}
    if con_centroide:
        c["centroide"] = {"valor": {"lat": LAT, "lng": LNG}, "fuente": "manual", "fecha_dato": "2026-11-14"}
    return Colonia.model_validate(c)


def estaciones(filas):
    return pd.DataFrame(filas, columns=["nombre", "lat", "lng", "modo"])


def al_norte(m):
    return LAT + m * M_LAT


GTFS = estaciones(
    [
        ("Insurgentes", al_norte(480), LNG, Modo.metro),
        ("Durango", al_norte(220), LNG, Modo.metrobus),
        ("Durango", al_norte(240), LNG, Modo.metrobus),  # otro andén a 20 m: duplicado
        ("Durango", al_norte(240), LNG, Modo.trolebus),  # mismo nombre, otro modo: se queda
        ("Glorieta", al_norte(300), LNG, Modo.metrobus),
        ("Glorieta", al_norte(400), LNG, Modo.metrobus),  # mismo nombre a 100 m: se queda
        ("Lejana", al_norte(900), LNG, Modo.metro),  # fuera de 800 m
    ]
)


def test_radio_fusion_y_orden():
    lista = tr.estaciones_cercanas(GTFS, LAT, LNG)
    assert [(e.nombre, e.tipo.value) for e in lista] == [
        ("Durango", "metrobus"),
        ("Durango", "trolebus"),
        ("Glorieta", "metrobus"),
        ("Glorieta", "metrobus"),
        ("Insurgentes", "metro"),
    ]
    assert abs(lista[0].distancia_m - 220) <= 3  # grados->metros aproximado en la prueba
    assert all(e.distancia_m <= 800 for e in lista)


def test_sin_estaciones_es_lista_vacia():
    assert tr.estaciones_cercanas(GTFS, 19.30, -99.30) == []
    assert tr.estaciones_cercanas(estaciones([]), LAT, LNG) == []


def test_inferir_modos_por_agencia_y_route_type():
    stops = pd.DataFrame(
        {"stop_id": ["s1", "s2", "s3", "s4"], "stop_name": ["A", "B", "C", "D"],
         "stop_lat": ["19.4", "19.41", "19.42", "19.43"], "stop_lon": ["-99.1"] * 4}
    )
    routes = pd.DataFrame(
        {"route_id": ["r1", "r2", "r3", "r4"], "agency_id": ["METRO", "SEMOVI", "RTP", "CBB"],
         "route_type": ["1", "11", "3", "6"]}
    )
    trips = pd.DataFrame({"trip_id": ["t1", "t2", "t3", "t4"], "route_id": ["r1", "r2", "r3", "r4"]})
    stop_times = pd.DataFrame({"trip_id": ["t1", "t1", "t2", "t3", "t4"], "stop_id": ["s1", "s1", "s2", "s3", "s4"]})
    df, descartadas = tr.inferir_modos(stops, stop_times, trips, routes)
    assert dict(zip(df["nombre"], df["modo"])) == {"A": Modo.metro, "B": Modo.trolebus, "D": Modo.cablebus}
    assert descartadas == 1  # la parada de RTP


def test_estaciones_ecobici():
    df = tr.estaciones_ecobici(
        {"data": {"stations": [{"name": "001 Río Sena", "lat": 19.43, "lon": -99.17}, {"name": "sin coord"}]}}
    )
    assert len(df) == 1 and df.iloc[0]["modo"] == Modo.ecobici and df.iloc[0]["lng"] == -99.17


def test_modo_desde_nombre():
    assert tr.modo_desde_nombre("Metrobús Durango") == Modo.metrobus
    assert tr.modo_desde_nombre("Estación del Metro Insurgentes") == Modo.metro
    assert tr.modo_desde_nombre("Cablebús Línea 2") == Modo.cablebus
    assert tr.modo_desde_nombre("Buenavista") is None


def test_enriquecer_con_gtfs_y_ecobici():
    eco = estaciones([("Ecobici 1", al_norte(100), LNG, Modo.ecobici)]), date(2026, 11, 14)
    [c], motivos = tr.enriquecer_transporte([colonia()], gtfs=GTFS, ecobici=eco, cargar_archivos=False)
    dato = c.estaciones_transporte_cercanas
    assert dato.valor[0].tipo == Modo.ecobici and len(dato.valor) == 6
    assert tr.FUENTE_GTFS in dato.fuente and tr.FUENTE_ECOBICI in dato.fuente
    assert dato.fecha_dato == tr.FECHA_GTFS
    assert motivos == {}


def test_colonia_sin_estaciones_queda_lista_vacia_no_null():
    lejos = estaciones([("Lejana", al_norte(5000), LNG, Modo.metro)])
    [c], motivos = tr.enriquecer_transporte([colonia()], gtfs=lejos, cargar_archivos=False)
    assert c.estaciones_transporte_cercanas.valor == []
    assert c.estaciones_transporte_cercanas.fuente == tr.FUENTE_GTFS
    assert "lista vacía" in motivos["Roma Norte"][0]


def test_respaldo_osm_sin_gtfs():
    def osm(lat, lng, radio):
        return [
            {"categoria": "estacion_transporte", "nombre": "Metrobús Durango", "lat": al_norte(200), "lng": LNG},
            {"categoria": "estacion_transporte", "nombre": "Insurgentes", "lat": al_norte(480), "lng": LNG},
            {"categoria": "parque", "nombre": "Parque México", "lat": al_norte(100), "lng": LNG},
        ]

    [c], motivos = tr.enriquecer_transporte([colonia()], consultar_osm=osm, cargar_archivos=False)
    dato = c.estaciones_transporte_cercanas
    assert [e.nombre for e in dato.valor] == ["Metrobús Durango"]
    assert "respaldo" in dato.fuente
    assert any("modo no inferible" in m for m in motivos["Roma Norte"])


def test_respaldo_osm_que_falla_deja_null_sin_bucle():
    llamadas = []

    def osm(*args):
        llamadas.append(1)
        raise RuntimeError("502")

    [c], motivos = tr.enriquecer_transporte([colonia()], consultar_osm=osm, cargar_archivos=False)
    assert c.estaciones_transporte_cercanas.valor is None
    assert len(llamadas) == 2
    assert "falló 2 veces" in motivos["Roma Norte"][0]


def test_colonia_sin_centroide():
    [c], motivos = tr.enriquecer_transporte([colonia(con_centroide=False)], gtfs=GTFS, cargar_archivos=False)
    assert c.estaciones_transporte_cercanas.valor is None
    assert "centroide" in motivos["Roma Norte"][0]
