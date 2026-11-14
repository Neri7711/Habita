import pandas as pd
import pytest

from arraigo.pipeline.enriquecer.geo import area_km2, asignar_a_colonia, haversine_m, punto_en_poligono

# Cuadrado de juguete de 0.01° x 0.01° en CDMX, con un hueco de 0.002° en el centro
CUADRADO = {
    "type": "Polygon",
    "coordinates": [
        [[-99.17, 19.41], [-99.16, 19.41], [-99.16, 19.42], [-99.17, 19.42], [-99.17, 19.41]],
    ],
}
CON_HUECO = {
    "type": "Polygon",
    "coordinates": [
        CUADRADO["coordinates"][0],
        [[-99.166, 19.414], [-99.164, 19.414], [-99.164, 19.416], [-99.166, 19.416], [-99.166, 19.414]],
    ],
}
VECINO = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[-99.16, 19.41], [-99.15, 19.41], [-99.15, 19.42], [-99.16, 19.42], [-99.16, 19.41]]],
        [[[-99.10, 19.43], [-99.09, 19.43], [-99.09, 19.44], [-99.10, 19.44], [-99.10, 19.43]]],
    ],
}


def test_haversine_un_grado_de_latitud():
    # 1° sobre un meridiano = R * pi / 180 ≈ 111,195 m
    assert haversine_m(19.0, -99.0, 20.0, -99.0) == pytest.approx(111_195, rel=0.01)


def test_haversine_cero_y_simetria():
    assert haversine_m(19.43, -99.13, 19.43, -99.13) == 0
    assert haversine_m(19.43, -99.13, 19.42, -99.16) == pytest.approx(haversine_m(19.42, -99.16, 19.43, -99.13))


def test_punto_dentro_y_fuera():
    assert punto_en_poligono(19.415, -99.165, CUADRADO)
    assert not punto_en_poligono(19.43, -99.165, CUADRADO)


def test_hueco_no_cuenta_como_dentro():
    assert not punto_en_poligono(19.415, -99.165, CON_HUECO)
    assert punto_en_poligono(19.411, -99.169, CON_HUECO)


def test_asignar_a_colonia():
    puntos = pd.DataFrame(
        {
            "lat": [19.415, 19.415, 19.435, 19.50, None],
            "lng": [-99.165, -99.155, -99.095, -99.165, -99.165],
        },
        index=[10, 11, 12, 13, 14],
    )
    asignado = asignar_a_colonia(puntos, {"A": CUADRADO, "B": VECINO})
    assert list(asignado.index) == [10, 11, 12, 13, 14]
    assert asignado[10] == "A"
    assert asignado[11] == "B"
    assert asignado[12] == "B"  # segunda parte del multipolígono
    assert pd.isna(asignado[13])  # fuera de todo
    assert pd.isna(asignado[14])  # sin coordenada


def test_asignar_vacio():
    assert asignar_a_colonia(pd.DataFrame({"lat": [], "lng": []}), {"A": CUADRADO}).empty


def test_area_km2():
    # 0.01° lat ≈ 1.106 km; 0.01° lng en lat 19.415 ≈ 1.050 km  => ≈ 1.161 km²
    assert area_km2(CUADRADO) == pytest.approx(1.161, rel=0.01)
    hueco = area_km2({"type": "Polygon", "coordinates": [CON_HUECO["coordinates"][1]]})
    assert area_km2(CON_HUECO) == pytest.approx(area_km2(CUADRADO) - hueco)
    assert area_km2(VECINO) == pytest.approx(2 * area_km2(CUADRADO), rel=0.01)


def test_geometria_no_soportada():
    with pytest.raises(ValueError):
        area_km2({"type": "Point", "coordinates": [-99.1, 19.4]})
