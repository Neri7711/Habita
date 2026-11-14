import math
from datetime import date
from pathlib import Path

import pytest

from arraigo.calculos import costo_real, haversine_km, mensualidad, precio_justo
from arraigo.calculos.traslado import RADIO_TIERRA_KM
from arraigo.schemas import Colonia, Dato, Inmueble, Perfil

KM_POR_GRADO = RADIO_TIERRA_KM * math.pi / 180
DESTINO = (19.40, -99.16)


def inmueble(**cambios):
    base = dict(id="t1", operacion="renta", precio_mxn=18000, colonia="Roma Norte", alcaldia="Cuauhtémoc",
                lat=DESTINO[0] + 6.0 / KM_POR_GRADO, lng=DESTINO[1], m2=60, recamaras=2, banos=1,
                fuente="captura_manual:prueba", fecha_captura="2026-11-14")
    return Inmueble.model_validate(base | cambios)


def perfil(**cambios):
    base = dict(operacion_deseada="renta", presupuesto_max_mxn=20000, ingreso_mensual_mxn=30000,
                destino_trabajo={"lat": DESTINO[0], "lng": DESTINO[1]}, modo_transporte="transporte_publico",
                tiempo_max_traslado_min=45, prioridades=["precio"])
    return Perfil.model_validate(base | cambios)


def colonia(renta=360.0, venta=60000.0):
    return Colonia(nombre="Roma Norte", alcaldia="Cuauhtémoc",
                   precio_m2_renta_mediana=Dato[float](valor=renta, fuente="prueba", fecha_dato=date(2026, 11, 14)),
                   precio_m2_venta_mediana=Dato[float](valor=venta, fuente="prueba", fecha_dato=date(2026, 11, 14)))


def test_haversine():
    assert haversine_km(*DESTINO, DESTINO[0] + 6.0 / KM_POR_GRADO, DESTINO[1]) == pytest.approx(6.0)


def test_ejemplo_de_design_md():
    r = costo_real(inmueble(), perfil(), colonia())
    assert r["traslado"]["minutos_ida"] == 30
    assert r["transporte"]["monto_mxn"] == 220
    assert r["servicios"]["monto_mxn"] == 1400
    assert r["tiempo_valorizado"]["monto_mxn"] == 3750
    assert r["costo_monetario_mxn"] == 19620 and r["costo_real_mxn"] == 23370
    assert r["precio_justo"]["banda"] == "justo" and not r["excede_presupuesto"]


@pytest.mark.parametrize("precio,banda", [(12600, "justo"), (12599, "sospechosamente_barato"),
                                          (20700, "justo"), (20701, "caro")])
def test_bandas_precio_justo(precio, banda):
    # mediana 300/m2 × 60 m2 = 18,000 → límites 0.70 = 12,600 y 1.15 = 20,700
    assert precio_justo(inmueble(precio_mxn=precio), colonia(renta=300.0))["banda"] == banda


def test_no_evaluable_sin_m2_o_sin_mediana():
    assert precio_justo(inmueble(m2=None), colonia())["banda"] == "no_evaluable"
    assert precio_justo(inmueble(), None)["banda"] == "no_evaluable"


def test_sin_ubicacion():
    r = costo_real(inmueble(lat=None, lng=None), perfil())
    assert r["traslado"] is None and r["costo_real_mxn"] is None
    assert r["transporte"]["motivo_no_calculable"] == "sin ubicación"
    assert r["costo_monetario_mxn"] is None


def test_compra():
    assert mensualidad(1_000_000, 1_000_000) == 0
    assert mensualidad(1_200_000, 0, tasa_anual_pct=0, plazo_anios=10) == 10_000
    r = costo_real(inmueble(operacion="venta", precio_mxn=4_000_000), perfil(operacion_deseada="compra",
                   enganche_disponible_mxn=800_000, presupuesto_max_mxn=5_000_000), colonia())
    assert r["hipoteca"]["monto_financiado_mxn"] == 3_200_000
    assert 30_000 < r["vivienda"]["monto_mxn"] < 40_000
    assert any("asesoría hipotecaria" in a for a in r["avisos"])
    sin = costo_real(inmueble(operacion="venta", precio_mxn=4_000_000), perfil())
    assert sin["vivienda"]["motivo_no_calculable"] == "sin enganche en el perfil"


def test_calculos_sin_red():
    for f in Path("src/arraigo/calculos").glob("*.py"):
        texto = f.read_text(encoding="utf-8")
        assert "arraigo.fuentes" not in texto and "urllib" not in texto and "requests" not in texto


def test_dataset_completo_perfil_roma_norte(tmp_path):
    from arraigo.pipeline.cargar import construir_colonias, validar_anuncios
    from arraigo.pipeline.colonias import cargar_catalogo
    from arraigo.pipeline.sinteticos import escribir_csv, generar

    cat = cargar_catalogo()
    escribir_csv(generar(cat, seed=42), tmp_path / "anuncios_sinteticos.csv")
    validos, _ = validar_anuncios(tmp_path, cat)
    colonias = {c.nombre: c for c in construir_colonias(cat, validos)}
    p = perfil(operacion_deseada="ambas", enganche_disponible_mxn=1_000_000, presupuesto_max_mxn=30000,
               ingreso_mensual_mxn=60000, destino_trabajo={"lat": 19.4326, "lng": -99.1332})
    resultados = [costo_real(i, p, colonias[i.colonia]) for i in validos]
    assert all(r["costo_monetario_mxn"] for r in resultados)
    assert {r["precio_justo"]["banda"] for r in resultados} >= {"justo", "sospechosamente_barato"}
