import pytest
from pydantic import ValidationError

from arraigo.schemas import Inmueble

MINIMO = {
    "id": "x1", "operacion": "renta", "precio_mxn": 15000, "colonia": "Roma Norte", "alcaldia": "Cuauhtémoc",
    "lat": 19.42, "lng": -99.16, "recamaras": 1, "banos": 1, "fuente": "sintetico", "fecha_captura": "2026-11-14",
}


def test_valido_minimo():
    i = Inmueble.model_validate(MINIMO)
    assert i.precio_mxn == 15000 and not i.ubicacion_aproximada


@pytest.mark.parametrize("cambio", [{"precio_mxn": 0}, {"colonia": ""}, {"lat": 20.5}])
def test_invalidos(cambio):
    with pytest.raises(ValidationError):
        Inmueble.model_validate(MINIMO | cambio)


def test_sin_coordenadas_usa_centroide():
    datos = MINIMO | {"lat": None, "lng": None}
    i = Inmueble.model_validate(datos, context={"centroides": {"Roma Norte": (19.4195, -99.162)}})
    assert (i.lat, i.lng) == (19.4195, -99.162) and i.ubicacion_aproximada
