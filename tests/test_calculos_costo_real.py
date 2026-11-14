import ast
import json
from pathlib import Path

import arraigo.calculos
from arraigo.calculos import calcular_costo_real, costo_real
from arraigo.schemas import Inmueble
from test_calculos_base import CONFIG, TARIFAS, TASA, colonia, inmueble, perfil


def _calc(inm=None, per=None, col="default", tasa=TASA):
    col = colonia() if col == "default" else col
    return calcular_costo_real(inm or inmueble(), per or perfil(), col, CONFIG, TARIFAS, tasa)


def test_ejemplo_del_diseno_renta():
    r = _calc()
    assert r.vivienda.monto_mxn == 18_000
    assert r.transporte.monto_mxn == 220
    assert r.servicios.monto_mxn == 1_400
    assert r.tiempo_valorizado.monto_mxn == 3_750
    assert r.horas_traslado_mes == 22
    assert r.costo_monetario_mxn == 19_620
    assert r.costo_real_mxn == 23_370
    assert r.pct_ingreso_monetario == 65.4 and r.pct_ingreso_real == 77.9
    assert r.precio_justo.banda == "justo"
    assert r.hipoteca is None and r.enganche_inicial_mxn is None
    assert not r.excede_presupuesto and not r.es_sintetico
    assert "$19,620" in r.resumen and "$23,370" in r.resumen and "22 horas" in r.resumen
    for c in (r.vivienda, r.transporte, r.servicios, r.tiempo_valorizado):
        assert c.fuente and c.fecha_dato


def test_pago_de_renta_sobre_35_pct_del_ingreso_se_marca():
    assert _calc().pago_excede_ingreso  # 18,000 > 10,500
    assert not _calc(per=perfil(ingreso_mensual_mxn=60_000)).pago_excede_ingreso


def test_compra_con_enganche_aparte():
    inm = inmueble(operacion="venta", precio_mxn=2_500_000, m2=60.0)
    per = perfil(operacion_deseada="compra", enganche_disponible_mxn=500_000, presupuesto_max_mxn=3_000_000)
    r = _calc(inm, per, colonia(renta_m2=None, venta_m2=41_000))
    assert r.hipoteca.monto_financiado_mxn == 2_000_000
    assert r.vivienda.monto_mxn == r.hipoteca.mensualidad_mxn
    assert r.servicios.monto_mxn == 1_400 + 1_250  # 2,500,000 × 0.6% / 12 = 1,250
    assert r.enganche_inicial_mxn == 500_000
    assert r.costo_monetario_mxn == r.vivienda.monto_mxn + 220 + 2_650
    assert any("enganche no está incluido" in a for a in r.avisos)
    assert any("no es asesoría hipotecaria" in a for a in r.avisos)
    assert "500,000 de enganche" in r.resumen


def test_compra_sin_tasa_usa_respaldo_y_avisa():
    inm = inmueble(operacion="venta", precio_mxn=2_500_000)
    per = perfil(operacion_deseada="compra", enganche_disponible_mxn=500_000)
    r = _calc(inm, per, tasa=None)
    assert r.hipoteca.es_tasa_respaldo and "Tasa de respaldo, no es dato de Banxico." in r.avisos


def test_compra_sin_enganche_no_es_calculable():
    inm = inmueble(operacion="venta", precio_mxn=2_500_000)
    r = _calc(inm, perfil())  # operacion_deseada = renta, sin enganche
    assert r.vivienda.monto_mxn is None and r.vivienda.motivo_no_calculable == "sin enganche"
    assert r.costo_real_mxn is None and r.costo_monetario_mxn is None
    assert "sin enganche" in r.resumen


def test_excede_presupuesto():
    assert _calc(per=perfil(presupuesto_max_mxn=17_999)).excede_presupuesto
    assert not _calc(per=perfil(presupuesto_max_mxn=18_000)).excede_presupuesto


def test_sin_ubicacion():
    r = _calc(inmueble(lat=None, lng=None))
    assert r.traslado is None
    assert r.transporte.monto_mxn is None and r.transporte.motivo_no_calculable == "sin ubicación"
    assert r.tiempo_valorizado.monto_mxn is None and r.horas_traslado_mes is None
    assert r.vivienda.monto_mxn == 18_000 and r.servicios.monto_mxn == 1_400
    assert r.costo_real_mxn is None and r.costo_monetario_mxn is None
    assert "sin ubicación" in r.resumen


def test_avisos_por_modo_y_tipo_de_anuncio():
    assert "No incluye estacionamiento, seguro ni tenencia." in _calc(per=perfil(modo_transporte="auto")).avisos
    assert any("modo mixto" in a for a in _calc(per=perfil(modo_transporte="mixto")).avisos)
    r = _calc(inmueble(fuente="sintetico", ubicacion_aproximada=True))
    assert r.es_sintetico
    assert any("sintético" in a for a in r.avisos) and any("Ubicación aproximada" in a for a in r.avisos)
    assert "Estimación con supuestos; revisa los detalles antes de decidir." in r.avisos


def test_excede_tiempo_max_se_avisa():
    r = _calc(per=perfil(tiempo_max_traslado_min=20))
    assert r.traslado.excede_tiempo_max and any("supera tu máximo" in a for a in r.avisos)


def test_determinismo():
    a, b = _calc(), _calc()
    assert a.model_dump_json() == b.model_dump_json()


def test_fachada_costo_real_con_tres_argumentos():
    """Contrato de la spec 05: costo_real(inmueble, perfil, colonia) con los archivos reales de data/raw/."""
    r = costo_real(inmueble(), perfil(), colonia())
    assert r.costo_real_mxn is not None and r.inmueble_id == "t-1"
    assert callable(arraigo.calculos.precio_justo)


def test_calculos_no_importa_red_ni_fuentes():
    prohibidos = ("urllib", "requests", "http", "socket", "arraigo.fuentes", "arraigo.pipeline")
    for archivo in Path(arraigo.calculos.__file__).parent.glob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            nombres = []
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                nombres = [nodo.module or ""]
            for n in nombres:
                assert not n.startswith(prohibidos), f"{archivo.name} importa {n}"


def test_todos_los_inmuebles_procesados_sin_errores():
    ruta = Path(__file__).resolve().parents[1] / "data" / "processed" / "inmuebles.json"
    if not ruta.exists():
        import pytest

        pytest.skip("falta data/processed/inmuebles.json (uv run python scripts/cargar_dataset.py)")
    per = perfil(operacion_deseada="ambas", enganche_disponible_mxn=500_000, presupuesto_max_mxn=5_000_000)
    inmuebles = [Inmueble.model_validate(d) for d in json.loads(ruta.read_text(encoding="utf-8"))]
    assert inmuebles
    for inm in inmuebles:
        r = calcular_costo_real(inm, per, None, CONFIG, TARIFAS, TASA)
        assert r.costo_real_mxn is not None and r.costo_real_mxn >= r.costo_monetario_mxn
        assert r.precio_justo.banda == "no_evaluable"  # sin colonia no se inventa referencia
