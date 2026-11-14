import pytest

from arraigo.calculos.tiempo import horas_traslado_mes, tiempo_valorizado
from test_calculos_base import CONFIG


def test_horas_de_traslado_al_mes():
    assert horas_traslado_mes(30, CONFIG) == 22  # 30 × 2 × 22 / 60


def test_tiempo_valorizado_ejemplo_del_diseno():
    c = tiempo_valorizado(30, 30_000, CONFIG)
    assert c.monto_mxn == 3750  # 30,000 / 176 × 22
    assert any("22 horas de traslado al mes" in s for s in c.supuestos)
    assert any("gasto de bolsillo" in s for s in c.supuestos)


def test_factor_de_valor_del_tiempo():
    cfg = CONFIG.model_copy(deep=True)
    cfg.tiempo.factor_valor_tiempo = 0.5
    assert tiempo_valorizado(30, 30_000, cfg).monto_mxn == 1875


def test_traslado_cero():
    c = tiempo_valorizado(0, 30_000, CONFIG)
    assert c.monto_mxn == 0 and horas_traslado_mes(0, CONFIG) == pytest.approx(0)

