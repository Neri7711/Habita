import math

import pandas as pd
import pytest

from arraigo.pipeline.enriquecer.normalizar import rango_percentil


def test_extremos_y_orden():
    r = rango_percentil(pd.Series([10, 30, 20, 1000]))
    assert list(r) == pytest.approx([0, 2 / 3, 1 / 3, 1])


def test_empates_reciben_rango_promedio():
    r = rango_percentil(pd.Series([1, 2, 2, 3], index=list("abcd")))
    assert r["b"] == r["c"] == pytest.approx(0.5)
    assert r["a"] == 0 and r["d"] == 1


def test_un_solo_valor_distinto():
    assert list(rango_percentil(pd.Series([7, 7, 7]))) == [0.5, 0.5, 0.5]
    assert list(rango_percentil(pd.Series([7]))) == [0.5]


def test_nan_se_conserva_y_no_cuenta():
    r = rango_percentil(pd.Series([5, None, 1, 9]))
    assert math.isnan(r[1])
    assert [r[2], r[0], r[3]] == pytest.approx([0, 0.5, 1])


def test_todo_nan_o_vacio():
    assert rango_percentil(pd.Series([None, None], dtype=float)).isna().all()
    assert rango_percentil(pd.Series([], dtype=float)).empty
