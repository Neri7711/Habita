import pytest

from arraigo.calculos.hipoteca import AVISO_ENGANCHE_MINIMO, AVISO_HIPOTECA, AVISO_RESPALDO, cuota_fija, mensualidad_compra
from arraigo.calculos.supuestos import tasa_respaldo
from test_calculos_base import CONFIG, TASA


def test_cuota_fija_valor_conocido():
    # $1,000,000 al 12% anual a 12 meses: cuota = 88,848.79 (valor clásico de amortización francesa)
    assert cuota_fija(1_000_000, 12, 1) == pytest.approx(88_848.79, abs=0.01)


def test_cuota_con_tasa_cero_es_lineal():
    assert cuota_fija(2_400_000, 0, 20) == 10_000  # 2,400,000 / 240


def test_mensualidad_a_mano():
    # tasa 8% + 3.5 = 11.5% anual; i = 0.0095833...; n = 240; P = 2,000,000
    h = mensualidad_compra(2_500_000, 500_000, TASA, CONFIG)
    assert h.tasa_anual_pct == pytest.approx(11.5)
    assert h.monto_financiado_mxn == 2_000_000 and h.plazo_anios == 20
    i = 0.115 / 12
    esperado = 2_000_000 * i / (1 - (1 + i) ** -240)
    assert h.mensualidad_mxn == int(esperado + 0.5)
    assert h.mensualidad_mxn == 21_329  # P·i / (1 − (1+i)^−240) con i = 0.115/12
    assert h.avisos == [AVISO_HIPOTECA]


def test_enganche_mayor_o_igual_al_precio_da_mensualidad_cero():
    for enganche in (1_000_000, 1_200_000):
        h = mensualidad_compra(1_000_000, enganche, TASA, CONFIG)
        assert h.mensualidad_mxn == 0 and h.monto_financiado_mxn == 0
        assert any("mensualidad es 0" in a for a in h.avisos)


def test_tasa_cero_en_mensualidad():
    cfg = CONFIG.model_copy(deep=True)
    cfg.compra.spread_sobre_tiie_pp = 0
    h = mensualidad_compra(2_400_000, 0, TASA.model_copy(update={"tasa_pct": 0}), cfg)
    assert h.mensualidad_mxn == 10_000


def test_enganche_menor_al_minimo_avisa_pero_calcula():
    h = mensualidad_compra(2_000_000, 100_000, TASA, CONFIG)  # 5% < 10%
    assert AVISO_ENGANCHE_MINIMO in h.avisos and h.mensualidad_mxn > 0
    assert AVISO_ENGANCHE_MINIMO not in mensualidad_compra(2_000_000, 200_000, TASA, CONFIG).avisos  # 10% exacto


def test_tasa_de_respaldo_avisa():
    h = mensualidad_compra(2_000_000, 400_000, tasa_respaldo(CONFIG), CONFIG)
    assert AVISO_RESPALDO in h.avisos and h.es_tasa_respaldo and h.fuente_tasa == "respaldo"

