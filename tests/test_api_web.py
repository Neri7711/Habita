"""Pruebas de humo de la API HTTP (usa los datos de data/processed; los genera si faltan)."""

import pytest
from starlette.testclient import TestClient

from arraigo.api_web import app, perfil_completo, resolver_zona

cliente = TestClient(app)


def test_salud_y_stats():
    assert cliente.get("/api/salud").json()["ok"] is True
    s = cliente.get("/api/stats").json()
    assert s["colonias"] == 13 and s["anuncios"] >= 200 and s["origen"] == "api"


def test_colonias_y_zonas():
    cols = cliente.get("/api/colonias").json()
    assert len(cols) == 13 and {"colonia", "alcaldia", "hipotesis_presion", "rol"} <= cols[0].keys()
    assert any(z["id"] == "reforma" for z in cliente.get("/api/zonas").json())


def test_buscar_regresa_tarjetas_con_supuestos():
    r = cliente.post("/api/buscar", json={"operacion": "renta", "presupuesto_max_mxn": 18000,
                                          "destino_trabajo": "Polanco", "mascotas": False}).json()
    assert r["opciones"], r
    t = r["opciones"][0]
    assert {"titulo", "colonia", "operacion", "precio_mxn", "chips", "datoComunidad", "fuente", "esEjemplo", "avisos"} <= t.keys()
    assert any("Polanco" in s for s in r["supuestos"])


def test_buscar_valida_presupuesto():
    assert cliente.post("/api/buscar", json={"operacion": "renta", "presupuesto_max_mxn": 5}).status_code == 400


def test_detalle_inmueble():
    r = cliente.get("/api/inmuebles/sint-0134").json()
    assert "señales" in r["confiabilidad"]["explicacion"] or r["confiabilidad"]["datos"]
    assert cliente.get("/api/inmuebles/no-existe").status_code == 404


def test_zona_por_id_y_perfil_compra():
    z, aviso = resolver_zona("santa-fe")
    assert z["id"] == "santa-fe" and aviso is None
    p, sup = perfil_completo({"operacion": "compra", "presupuesto_max_mxn": 3_000_000, "destino_trabajo": "reforma"})
    assert p["enganche_disponible_mxn"] == 600_000 and any("Enganche" in s for s in sup)
