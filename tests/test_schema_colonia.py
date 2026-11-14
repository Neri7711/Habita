import pytest
from pydantic import ValidationError

from arraigo.schemas import Colonia, Dato


def test_colonia_minima_con_campos_vacios():
    c = Colonia(nombre="Roma Norte", alcaldia="Cuauhtémoc")
    assert c.indice_delitos.valor is None


def test_valor_sin_fuente_es_error():
    with pytest.raises(ValidationError):
        Dato[float](valor=0.3)


def test_valor_con_fuente_y_fecha():
    assert Dato[float](valor=0.3, fuente="FGJ", fecha_dato="2026-11-14").valor == 0.3
