"""Gentrificación con datos de juguete (sin red ni archivos)."""

from datetime import date

import pandas as pd
import pytest

from arraigo.pipeline.enriquecer import gentrificacion as g
from arraigo.pipeline.enriquecer.geo import centroide
from arraigo.pipeline.enriquecer.poligonos import Unidad, mapear_colonia
from arraigo.schemas.colonia import Colonia


def cuadro(x0, y0, lado=0.01):
    return {
        "type": "Polygon",
        "coordinates": [[[x0, y0], [x0 + lado, y0], [x0 + lado, y0 + lado], [x0, y0 + lado], [x0, y0]]],
    }


# Colonia piloto "Roma Norte" partida en dos unidades IECM + dos unidades más del catálogo
UNIDADES = [
    Unidad("1", "ROMA NORTE I", "CUAUHTEMOC", cuadro(-99.17, 19.41), 1.0),
    Unidad("2", "ROMA NORTE II", "CUAUHTEMOC", cuadro(-99.16, 19.41), 1.0),
    Unidad("3", "OTRA", "CUAUHTEMOC", cuadro(-99.15, 19.41), 1.0),
    Unidad("4", "LEJANA", "IZTAPALAPA", cuadro(-99.05, 19.35), 1.0),
]


def colonia(nombre="Roma Norte", alcaldia="Cuauhtémoc", lat=19.415, lng=-99.165):
    return Colonia.model_validate(
        {"nombre": nombre, "alcaldia": alcaldia,
         "centroide": {"valor": {"lat": lat, "lng": lng}, "fuente": "manual", "fecha_dato": "2026-11-14"}}
    )


# ---------- fórmula ----------


def test_formula_tres_componentes():
    valor, faltantes = g.presion({"densidad_airbnb": 1.0, "cambio_educacion": 0.5, "cambio_poblacion": 0.0})
    assert valor == pytest.approx(0.40 + 0.175) and faltantes == []


def test_formula_un_faltante_reescala_pesos():
    valor, faltantes = g.presion({"densidad_airbnb": 1.0, "cambio_educacion": None, "cambio_poblacion": 0.0})
    assert valor == pytest.approx(round(0.40 / 0.65, 3))
    assert faltantes == ["cambio_educacion"]


def test_formula_todos_faltantes():
    assert g.presion({"densidad_airbnb": None}) == (None, ["densidad_airbnb", "cambio_educacion", "cambio_poblacion"])


def test_signo_cambio_poblacion_perder_residentes_es_mas_presion():
    crudos = pd.DataFrame(
        {"listings_por_km2": [1, 2, 3], "delta_pp_educacion_superior": [1, 2, 3],
         "cambio_pct_poblacion": [-0.2, 0.0, 0.3]},
        index=["pierde", "igual", "gana"],
    )
    comps = g.componentes_normalizados(crudos)
    assert comps.loc["pierde", "cambio_poblacion"] == 1.0
    assert comps.loc["gana", "cambio_poblacion"] == 0.0
    assert comps.loc["gana", "densidad_airbnb"] == 1.0


def test_coincide_hipotesis():
    assert g.coincide_hipotesis("alta", 0.7) is True
    assert g.coincide_hipotesis("alta", 0.5) is False
    assert g.coincide_hipotesis("media", 0.4) is True
    assert g.coincide_hipotesis("baja", 0.62) is False
    assert g.coincide_hipotesis("baja", None) is None


# ---------- censo ----------


def test_agregar_censo_pareado_y_cobertura():
    c10 = pd.DataFrame({"pob": [100, 100, 50], "p18": [80, 80, 40], "pb": [20, 40, 10]}, index=["a", "b", "c"])
    c20 = pd.DataFrame(
        {"pob": [90, 110, 60, 1000], "p18": [75, 90, 50, 800], "pb": [30, 45, 20, 400]}, index=["a", "b", "c", "d"]
    )
    grupo = pd.Series({"a": "G1", "b": "G1", "c": "G2", "d": "G2"})
    r = g.agregar_censo(c10, c20, grupo)
    # G1: pareados a+b; población 200 -> 200 (cambio 0); posbásica 60/160 -> 75/165
    assert r.loc["G1", "cambio_pct_poblacion"] == pytest.approx(0.0)
    assert r.loc["G1", "delta_pp_educacion_superior"] == pytest.approx(100 * (75 / 165 - 60 / 160))
    # G2: el AGEB "d" no existe en 2010 -> cobertura 60/1060 < 50%: componentes censales faltantes
    assert r.loc["G2", "cobertura"] == pytest.approx(60 / 1060)
    assert pd.isna(r.loc["G2", "cambio_pct_poblacion"]) and pd.isna(r.loc["G2", "delta_pp_educacion_superior"])
    assert r.loc["G2", "poblacion_2020"] == 1060


def test_agregar_censo_valores_reservados_no_cuentan():
    c10 = pd.DataFrame({"pob": [100, float("nan")], "p18": [80, 10], "pb": [20, 5]}, index=["a", "b"])
    c20 = pd.DataFrame({"pob": [120, 10], "p18": [90, 8], "pb": [30, 4]}, index=["a", "b"])
    r = g.agregar_censo(c10, c20, pd.Series({"a": "G", "b": "G"}))
    assert r.loc["G", "cambio_pct_poblacion"] == pytest.approx(0.2)


# ---------- polígonos ----------


def test_mapear_por_nombre_une_unidades_romanas():
    m = mapear_colonia(UNIDADES, "Roma Norte", "Cuauhtémoc", 19.415, -99.165)
    assert m.unidades == ["1", "2"] and m.metodo == "nombre"


def test_mapear_por_centroide_si_no_hay_nombre():
    m = mapear_colonia(UNIDADES, "Colonia Inventada", "Cuauhtémoc", 19.415, -99.145)
    assert m.unidades == ["3"] and m.metodo == "centroide"


def test_mapear_sin_seccion_y_sin_poligono():
    unidades = [Unidad("9", "ESCANDON I", "MIGUEL HIDALGO", cuadro(-99.18, 19.40), 1.0)]
    assert mapear_colonia(unidades, "Escandón I Sección", "Miguel Hidalgo", 19.405, -99.175).metodo == "nombre_sin_seccion"
    assert mapear_colonia(unidades, "X", "Miguel Hidalgo", 19.9, -99.9).metodo == "sin_poligono"


def test_centroide_de_cuadro():
    lat, lng = centroide(cuadro(-99.17, 19.41))
    assert lat == pytest.approx(19.415) and lng == pytest.approx(-99.165)


# ---------- orquestación del campo ----------


def _airbnb():
    filas = [(i, 19.412 + i * 1e-4, -99.168) for i in range(6)]  # 6 en Roma Norte I
    filas += [(100 + i, 19.415, -99.145) for i in range(2)]  # 2 en OTRA
    return pd.DataFrame(filas, columns=["id", "lat", "lng"])


def test_enriquecer_solo_airbnb_sin_censo():
    [c], motivos, comp = g.enriquecer_gentrificacion(
        [colonia()], unidades=UNIDADES, airbnb=_airbnb(), hipotesis={"roma norte": "alta"}, cargar_archivos=False
    )
    d = c.presion_gentrificacion_detalle.valor
    assert d.componentes_faltantes == ["cambio_educacion", "cambio_poblacion"]
    assert d.crudos["listings_por_km2"] == pytest.approx(3.0)  # 6 anuncios / 2 km²
    assert d.componentes["densidad_airbnb"] == 1.0  # el más denso de 3 grupos
    assert c.indicador_presion_gentrificacion.valor == 1.0
    assert c.indicador_presion_gentrificacion.fuente == g.FUENTE_AIRBNB
    assert c.indicador_presion_gentrificacion.fecha_dato == date(2026, 9, 23)
    assert "no hubo datos del censo" in c.indicador_presion_gentrificacion.explicacion
    assert d.es_heuristica
    assert comp[0]["coincide"] is True


def test_enriquecer_con_censo():
    claves = ["r1", "r2", "o", "l"]
    centroides = pd.DataFrame(
        {"lat": [19.415, 19.415, 19.415, 19.355], "lng": [-99.165, -99.155, -99.145, -99.045]}, index=claves
    )
    c10 = pd.DataFrame({"pob": [100, 100, 100, 100], "p18": [80] * 4, "pb": [20] * 4}, index=claves)
    c20 = pd.DataFrame({"pob": [80, 80, 100, 120], "p18": [70, 70, 80, 90], "pb": [40, 40, 20, 20]}, index=claves)
    [c], _, _ = g.enriquecer_gentrificacion(
        [colonia()], unidades=UNIDADES, airbnb=_airbnb(), censo_2010=c10, censo_2020=c20,
        centroides_ageb=centroides, hipotesis={}, cargar_archivos=False,
    )
    d = c.presion_gentrificacion_detalle.valor
    assert d.componentes_faltantes == []
    assert d.crudos["cambio_pct_poblacion"] == pytest.approx(-0.2)
    assert d.componentes == {"densidad_airbnb": 1.0, "cambio_educacion": 1.0, "cambio_poblacion": 1.0}
    assert c.indicador_presion_gentrificacion.valor == 1.0
    assert g.FUENTE_CENSO in c.indicador_presion_gentrificacion.fuente


def test_colonia_sin_poligono_queda_null_con_motivo():
    [c], motivos, comp = g.enriquecer_gentrificacion(
        [colonia("Nada", lat=19.9, lng=-99.9)], unidades=UNIDADES, airbnb=_airbnb(), hipotesis={},
        cargar_archivos=False,
    )
    assert c.indicador_presion_gentrificacion.valor is None
    assert "sin polígono" in motivos["Nada"][0]
    assert comp[0]["valor"] is None
