"""Comunidad con respuestas simuladas de Overpass y DENUE (sin red)."""

from datetime import date

import pytest

from arraigo.pipeline.enriquecer import comunidad as com
from arraigo.schemas.colonia import Colonia

HOY = date(2026, 11, 14)
LAT, LNG = 19.4195, -99.1620

OSM = [
    {"categoria": "parque", "nombre": "Parque México", "lat": 19.4120, "lng": -99.1700},
    {"categoria": "mercado", "nombre": "Mercado Medellín", "lat": 19.4150, "lng": -99.1640},
    {"categoria": "mercado", "nombre": "Mercado Medellín", "lat": 19.4150, "lng": -99.1640},  # duplicado
    {"categoria": "centro_cultural", "nombre": None, "lat": 19.4200, "lng": -99.1625},
    {"categoria": "estacion_transporte", "nombre": "Insurgentes", "lat": 19.4235, "lng": -99.1630},
]
DENUE = {
    "mercado": [{"Id": "1"}, {"Id": "2"}],
    "abarrotes": [{"Id": "2"}, {"Id": "3"}, {"Id": "4"}],  # el 2 ya contó como mercado
    "fonda": [],
}


def osm_ok(lat, lng, radio):
    return OSM


def denue_ok(lat, lng, radio, palabra):
    return DENUE.get(palabra, [])


def colonia(nombre="Roma Norte", con_centroide=True):
    c = {"nombre": nombre, "alcaldia": "Cuauhtémoc"}
    if con_centroide:
        c["centroide"] = {"valor": {"lat": LAT, "lng": LNG}, "fuente": "manual", "fecha_dato": HOY}
    return Colonia.model_validate(c)


class Contador:
    """Consultor que siempre falla y cuenta llamadas."""

    def __init__(self):
        self.llamadas = 0

    def __call__(self, *args):
        self.llamadas += 1
        raise RuntimeError("502 Bad Gateway")


def test_puntos_desde_osm_filtra_dedup_y_ordena():
    puntos = com.puntos_desde_osm(OSM, LAT, LNG)
    assert [p.tipo.value for p in puntos] == ["centro_cultural", "mercado", "parque"]
    assert [p.distancia_m for p in puntos] == sorted(p.distancia_m for p in puntos)
    assert puntos[0].nombre is None


def test_puntos_desde_osm_limite_por_categoria():
    muchos = [{"categoria": "parque", "nombre": f"P{i}", "lat": LAT + i * 1e-4, "lng": LNG} for i in range(20)]
    puntos = com.puntos_desde_osm(muchos, LAT, LNG, max_por_categoria=15)
    assert len(puntos) == 15 and puntos[-1].nombre == "P14"


def test_resumir_denue_sin_duplicar():
    r = com.resumir_denue(DENUE)
    assert r.total_negocios == 4
    assert r.por_tipo == {"mercado": 2, "abarrotes": 2, "fonda": 0}
    assert r.radio_m == 500


def test_con_reintentos_maximo_dos():
    falla = Contador()
    resultado, motivo = com.con_reintentos(falla)
    assert resultado is None and falla.llamadas == 2 and "502" in motivo


def test_con_reintentos_oculta_token(monkeypatch):
    monkeypatch.setenv("INEGI_TOKEN", "secreto-123")

    def falla():
        raise RuntimeError("url .../secreto-123")

    _, motivo = com.con_reintentos(falla)
    assert "secreto-123" not in motivo and "***" in motivo


def test_colonia_con_token():
    [c], motivos = com.enriquecer_comunidad(
        [colonia()], hoy=HOY, consultar_osm=osm_ok, consultar_denue=denue_ok, hay_token=True, avisar=lambda m: None
    )
    assert len(c.puntos_comunidad.valor) == 3
    assert c.puntos_comunidad.fuente == com.FUENTE_OSM and c.puntos_comunidad.fecha_dato == HOY
    assert c.comercio_local.valor.total_negocios == 4 and c.comercio_local.fuente == com.FUENTE_DENUE
    assert motivos == {}


def test_colonia_sin_token_sigue_con_osm():
    avisos = []
    denue = Contador()
    [c], motivos = com.enriquecer_comunidad(
        [colonia()], hoy=HOY, consultar_osm=osm_ok, consultar_denue=denue, hay_token=False, avisar=avisos.append
    )
    assert denue.llamadas == 0
    assert c.comercio_local.valor is None
    assert c.puntos_comunidad.valor and "sin DENUE" in c.puntos_comunidad.fuente
    assert any("INEGI_TOKEN" in a for a in avisos)
    assert any("comercio_local" in m for m in motivos["Roma Norte"])


def test_lista_vacia_es_dato_valido_y_se_avisa():
    [c], motivos = com.enriquecer_comunidad(
        [colonia()], hoy=HOY, consultar_osm=lambda *a: [], consultar_denue=denue_ok, hay_token=True, avisar=print
    )
    assert c.puntos_comunidad.valor == [] and c.puntos_comunidad.fuente
    assert any("0 puntos" in m for m in motivos["Roma Norte"])


def test_fallo_osm_deja_null_con_motivo_y_no_reintenta_en_bucle():
    osm = Contador()
    colonias = [colonia(f"C{i}") for i in range(5)]
    salida, motivos = com.enriquecer_comunidad(
        colonias, hoy=HOY, consultar_osm=osm, consultar_denue=denue_ok, hay_token=True, avisar=lambda m: None
    )
    # 2 intentos x 2 colonias; después se omite la fuente
    assert osm.llamadas == com.MAX_INTENTOS * com.MAX_FALLOS_SEGUIDOS
    assert all(c.puntos_comunidad.valor is None for c in salida)
    assert all(c.comercio_local.valor is not None for c in salida)  # DENUE sigue aunque OSM falle
    assert "falló 2 veces" in motivos["C0"][0]
    assert "omitido" in motivos["C4"][0]


def test_fallo_denue_corta_las_palabras_restantes():
    denue = Contador()
    [c], motivos = com.enriquecer_comunidad(
        [colonia()], hoy=HOY, consultar_osm=osm_ok, consultar_denue=denue, hay_token=True, avisar=lambda m: None
    )
    assert denue.llamadas == com.MAX_INTENTOS  # no pasa a las demás palabras
    assert c.comercio_local.valor is None and c.puntos_comunidad.valor
    assert any("DENUE" in m for m in motivos["Roma Norte"])


def test_colonia_sin_centroide():
    osm = Contador()
    [c], motivos = com.enriquecer_comunidad(
        [colonia(con_centroide=False)], hoy=HOY, consultar_osm=osm, hay_token=False, avisar=lambda m: None
    )
    assert osm.llamadas == 0 and c.puntos_comunidad.valor is None
    assert "centroide" in motivos["Roma Norte"][0]


@pytest.mark.parametrize("respuesta", [None, {"error": "x"}])
def test_denue_respuesta_no_lista_cuenta_cero(respuesta):
    r = com.enriquecer_colonia(LAT, LNG, hoy=HOY, consultar_osm=osm_ok, consultar_denue=lambda *a: respuesta)
    assert r.comercio.valor.total_negocios == 0
