import json

import pytest

from arraigo.calculos.supuestos import tasa_respaldo
from arraigo.pipeline import referencias
from arraigo.pipeline.referencias import DireccionNoEncontrada, geocodificar_destino, obtener_tasa_referencia
from test_calculos_base import CONFIG, colonia, inmueble


def test_geocodificar_ok(monkeypatch):
    consultas = []

    def falso(q):
        consultas.append(q)
        return {"lat": 19.43, "lng": -99.13, "nombre": "Zócalo, Ciudad de México"}

    monkeypatch.setattr(referencias.nominatim, "geocodificar", falso)
    u = geocodificar_destino("Plaza de la Constitución 1")
    assert (u.lat, u.lng) == (19.43, -99.13) and u.direccion.startswith("Zócalo")
    assert consultas == ["Plaza de la Constitución 1, Ciudad de México"]


def test_geocodificar_no_encontrada_pide_mas_detalle(monkeypatch):
    monkeypatch.setattr(referencias.nominatim, "geocodificar", lambda q: None)
    with pytest.raises(DireccionNoEncontrada, match="más detalle"):
        geocodificar_destino("asdfgh")


def test_geocodificar_vacia_no_llama_a_la_red(monkeypatch):
    def no_debe_llamarse(q):
        raise AssertionError("no debe consultar la red")

    monkeypatch.setattr(referencias.nominatim, "geocodificar", no_debe_llamarse)
    with pytest.raises(DireccionNoEncontrada):
        geocodificar_destino("  ")


def test_geocodificar_fuera_de_la_zona(monkeypatch):
    monkeypatch.setattr(referencias.nominatim, "geocodificar", lambda q: {"lat": 25.67, "lng": -100.31, "nombre": "Monterrey"})
    with pytest.raises(DireccionNoEncontrada, match="fuera de la zona"):
        geocodificar_destino("Centro, Monterrey")


def test_tasa_desde_banxico_se_guarda(monkeypatch, tmp_path):
    ruta = tmp_path / "tasa.json"
    monkeypatch.setattr(
        referencias.banxico, "dato_oportuno", lambda serie: {"serie": serie, "titulo": "TIIE", "fecha": "14/11/2026", "dato": "11.2525"}
    )
    t = obtener_tasa_referencia(CONFIG, ruta)
    assert t.tasa_pct == 11.2525 and t.fecha.isoformat() == "2026-11-14" and not t.es_respaldo
    assert "SF43783" in t.fuente
    assert json.loads(ruta.read_text(encoding="utf-8"))["tasa_pct"] == 11.2525


def test_sin_token_usa_la_ultima_tasa_guardada(monkeypatch, tmp_path):
    ruta = tmp_path / "tasa.json"
    ruta.write_text(
        json.dumps({"tasa_pct": 10.5, "fecha": "2026-10-01", "fuente": "Banco de México, SIE, serie SF43783"}), encoding="utf-8"
    )

    def sin_token(serie):
        raise RuntimeError("Falta BANXICO_TOKEN")

    monkeypatch.setattr(referencias.banxico, "dato_oportuno", sin_token)
    t = obtener_tasa_referencia(CONFIG, ruta)
    assert t.tasa_pct == 10.5 and not t.es_respaldo


def test_sin_token_ni_archivo_usa_respaldo(monkeypatch, tmp_path):
    def sin_red(serie):
        raise OSError("sin red")

    monkeypatch.setattr(referencias.banxico, "dato_oportuno", sin_red)
    t = obtener_tasa_referencia(CONFIG, tmp_path / "no_existe.json")
    assert t == tasa_respaldo(CONFIG) and t.es_respaldo and t.fuente == "respaldo"
    assert not (tmp_path / "no_existe.json").exists()


def test_archivo_corrupto_cae_al_respaldo(monkeypatch, tmp_path):
    ruta = tmp_path / "tasa.json"
    ruta.write_text("no es json", encoding="utf-8")
    monkeypatch.setattr(referencias.banxico, "dato_oportuno", lambda s: (_ for _ in ()).throw(RuntimeError("x")))
    assert obtener_tasa_referencia(CONFIG, ruta).es_respaldo


def test_completar_medianas_conserva_las_existentes():
    inm = [inmueble(id=f"a{i}", precio_mxn=20_000 + i * 100, m2=50.0, colonia="Roma Norte") for i in range(30)]
    col = colonia(renta_m2=999.0)
    out = referencias.completar_medianas([col], inm)
    assert out[0].precio_m2_renta_mediana.valor == 999.0  # no se pisa
