import pytest

from arraigo.calculos.traslado import SinUbicacion, estimar_traslado, haversine_km, redondear
from test_calculos_base import CONFIG, inmueble, perfil


def test_haversine_un_grado_de_latitud():
    assert haversine_km(19.0, -99.0, 20.0, -99.0) == pytest.approx(111.195, abs=0.01)


def test_haversine_mismo_punto_es_cero():
    assert haversine_km(19.4, -99.1, 19.4, -99.1) == 0


def test_redondeo_medio_sube():
    assert redondear(2.5) == 3 and redondear(29.65) == 30 and redondear(0.4) == 0


def test_transporte_publico_ejemplo_del_diseno():
    t = estimar_traslado(inmueble(), perfil(), CONFIG)
    assert t.distancia_recta_km == pytest.approx(6.0, abs=0.01)
    assert t.distancia_ruta_km == pytest.approx(8.4, abs=0.02)  # 6.0 × 1.4
    assert t.minutos_ida == 30  # round(8.4 / 17 × 60) = 29.65 → 30
    assert t.modo_usado == "transporte_publico"
    assert not t.excede_tiempo_max and t.avisos == []


def test_auto_y_bici_usan_su_propio_factor_y_velocidad():
    auto = estimar_traslado(inmueble(), perfil(modo_transporte="auto"), CONFIG)
    assert auto.distancia_ruta_km == pytest.approx(7.8, abs=0.02)  # 6.0 × 1.3
    assert auto.minutos_ida == 21  # 7.8 / 22 × 60 = 21.27
    bici = estimar_traslado(inmueble(), perfil(modo_transporte="bici"), CONFIG)
    assert bici.distancia_ruta_km == pytest.approx(7.5, abs=0.02)  # 6.0 × 1.25
    assert bici.minutos_ida == 32  # 7.5 / 14 × 60 = 32.14


def test_mixto_usa_transporte_publico_y_avisa():
    t = estimar_traslado(inmueble(), perfil(modo_transporte="mixto"), CONFIG)
    assert t.modo_usado == "transporte_publico" and t.minutos_ida == 30
    assert "Para modo mixto se usó el cálculo de transporte público." in t.avisos


def test_ubicacion_aproximada_avisa():
    t = estimar_traslado(inmueble(ubicacion_aproximada=True), perfil(), CONFIG)
    assert "Ubicación aproximada: el traslado puede variar." in t.avisos


def test_excede_tiempo_max():
    assert estimar_traslado(inmueble(), perfil(tiempo_max_traslado_min=29), CONFIG).excede_tiempo_max
    assert not estimar_traslado(inmueble(), perfil(tiempo_max_traslado_min=30), CONFIG).excede_tiempo_max


def test_sin_ubicacion_se_rechaza_con_motivo():
    with pytest.raises(SinUbicacion, match="sin ubicación"):
        estimar_traslado(inmueble(lat=None, lng=None), perfil(), CONFIG)
