import pytest
from pydantic import ValidationError

from arraigo.schemas import Perfil

VALIDO = {
    "operacion_deseada": "renta", "presupuesto_max_mxn": 20000, "ingreso_mensual_mxn": 60000,
    "destino_trabajo": {"lat": 19.43, "lng": -99.2, "direccion": "Polanco"},
    "modo_transporte": "transporte_publico", "tiempo_max_traslado_min": 45, "prioridades": ["precio", "traslado"],
}


def test_valido():
    assert Perfil.model_validate(VALIDO).recamaras_min == 0


@pytest.mark.parametrize("cambio", [
    {"operacion_deseada": "compra"},            # sin enganche
    {"prioridades": ["precio", "precio"]},
    {"tiempo_max_traslado_min": 0},
])
def test_invalidos(cambio):
    with pytest.raises(ValidationError):
        Perfil.model_validate(VALIDO | cambio)


def test_compra_con_enganche():
    assert Perfil.model_validate(VALIDO | {"operacion_deseada": "compra", "enganche_disponible_mxn": 500000})
