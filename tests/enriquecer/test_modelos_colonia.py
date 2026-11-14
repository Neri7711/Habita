"""Ampliación del esquema Colonia para la spec 02 (tarea 1.1)."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from arraigo.schemas.colonia import (
    ComercioLocal,
    Colonia,
    Dato,
    DetalleDelitos,
    Estacion,
    NivelRiesgo,
    PresionGentrificacion,
    PuntoComunidad,
)

COLONIAS_JSON = Path(__file__).resolve().parents[2] / "data" / "processed" / "colonias.json"
HOY = "2026-11-14"


def test_campos_nuevos_vacios_por_defecto():
    c = Colonia(nombre="Roma Norte", alcaldia="Cuauhtémoc")
    assert c.indice_delitos_detalle.valor is None
    assert c.presion_gentrificacion_detalle.valor is None
    assert c.comercio_local.valor is None


def test_estacion_valida_modo():
    e = Estacion(nombre="Insurgentes", tipo="metro", punto={"lat": 19.42, "lng": -99.16}, distancia_m=420)
    assert e.tipo == "metro"
    with pytest.raises(ValidationError):
        Estacion(nombre="X", tipo="pesero", punto={"lat": 19.42, "lng": -99.16})


def test_nivel_riesgo_valida_nivel():
    assert NivelRiesgo(sismico="alto", clase_sismico="Zona III (lacustre)").sismico == "alto"
    with pytest.raises(ValidationError):
        NivelRiesgo(sismico="muy alto")


def test_punto_comunidad_sin_nombre():
    p = PuntoComunidad(tipo="parque", punto={"lat": 19.41, "lng": -99.17})
    assert p.nombre is None
    with pytest.raises(ValidationError):
        PuntoComunidad(tipo="cantina", punto={"lat": 19.41, "lng": -99.17})


def test_lista_vacia_distinta_de_null():
    vacia = Dato[list[Estacion]](valor=[], fuente="GTFS", fecha_dato=HOY)
    assert vacia.valor == [] and Dato[list[Estacion]]().valor is None


def test_presion_gentrificacion_rango():
    PresionGentrificacion(valor=0.7, componentes={"densidad_airbnb": 0.9})
    with pytest.raises(ValidationError):
        PresionGentrificacion(valor=1.2, componentes={})


def test_detalles_y_explicacion():
    d = Dato[DetalleDelitos](
        valor={"delitos_12m": 120, "tasa": 3.4, "base": "por_km2"},
        fuente="FGJ",
        fecha_dato=HOY,
        explicacion="Mide delitos registrados.",
    )
    assert d.valor.delitos_12m == 120 and d.explicacion
    assert ComercioLocal(radio_m=500, total_negocios=3, por_tipo={"fonda": 3}).total_negocios == 3


def test_colonias_json_de_spec_01_sigue_validando():
    if not COLONIAS_JSON.exists():
        pytest.skip("falta data/processed/colonias.json")
    for c in json.loads(COLONIAS_JSON.read_text(encoding="utf-8")):
        Colonia.model_validate(c)
