import pytest

from arraigo.calculos import precio_justo
from arraigo.calculos.banda_precio import evaluar_precio_justo
from test_calculos_base import CONFIG, colonia, inmueble


def _banda(precio_m2: float, mediana: float = 100.0, operacion="renta", **kw):
    """m2 = 100 para que precio = precio_m2 × 100."""
    inm = inmueble(operacion=operacion, precio_mxn=int(precio_m2 * 100), m2=100.0, **kw)
    col = colonia(renta_m2=mediana if operacion == "renta" else None, venta_m2=mediana if operacion == "venta" else None)
    return evaluar_precio_justo(inm, col, CONFIG)


def test_ejemplo_del_diseno_es_justo():
    r = evaluar_precio_justo(inmueble(), colonia(360.0), CONFIG)  # 18,000 / 60 = 300; 300 / 360 = 0.83
    assert r.banda == "justo" and r.razon == pytest.approx(0.8333, abs=1e-4)
    assert r.precio_m2 == 300 and r.mediana_m2 == 360 and r.n_anuncios_mediana == 12
    assert r.diferencia_pct == pytest.approx(-16.67, abs=0.01)
    assert "Roma Norte" in r.fuente_referencia and "2026-01-01" in r.fuente_referencia
    assert not r.es_sintetico


def test_limite_070():
    assert _banda(70).banda == "justo"  # razón exacta 0.70
    assert _banda(69.99).banda == "sospechosamente_barato"


def test_limite_115():
    assert _banda(115).banda == "justo"  # razón exacta 1.15
    assert _banda(115.01).banda == "caro"


def test_venta_usa_la_mediana_de_venta():
    assert _banda(50_000, mediana=40_000, operacion="venta").banda == "caro"  # 1.25
    assert _banda(40_000, mediana=40_000, operacion="venta").banda == "justo"


def test_barato_remite_al_antifraude_sin_juzgar():
    r = _banda(50)
    assert "antifraude" in r.explicacion and "oportunidad" in r.explicacion and "fraude" in r.explicacion


def test_sin_m2_no_es_evaluable():
    inm = inmueble(m2=None)
    r = evaluar_precio_justo(inm, colonia(), CONFIG)
    assert r.banda == "no_evaluable" and "metros cuadrados" in r.motivo_no_evaluable and r.razon is None


def test_sin_mediana_no_es_evaluable():
    r = evaluar_precio_justo(inmueble(), colonia(renta_m2=None), CONFIG)
    assert r.banda == "no_evaluable" and "precio de referencia" in r.motivo_no_evaluable
    # renta con mediana solo de venta
    assert evaluar_precio_justo(inmueble(), colonia(renta_m2=None, venta_m2=50_000), CONFIG).banda == "no_evaluable"


def test_sin_colonia_no_es_evaluable():
    assert evaluar_precio_justo(inmueble(), None, CONFIG).banda == "no_evaluable"


def test_sintetico_se_avisa():
    r = evaluar_precio_justo(inmueble(fuente="sintetico"), colonia(), CONFIG)
    assert r.es_sintetico and "sintético" in r.explicacion
    r2 = evaluar_precio_justo(inmueble(), colonia(fuente="anuncios sintéticos (n=5)"), CONFIG)
    assert r2.es_sintetico and r2.n_anuncios_mediana == 5


def test_fachada_publica_precio_justo_con_dos_argumentos():
    r = precio_justo(inmueble(), colonia(360.0))
    assert r.banda in {"justo", "caro", "sospechosamente_barato"}
