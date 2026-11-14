from arraigo.pipeline.colonias import cargar_catalogo, centroides, normalizar


def test_normalizar():
    assert normalizar("Col. Santa María  la Ribera") == "santa maria la ribera"


def test_13_colonias_con_centroide_en_cdmx():
    cat = cargar_catalogo()
    assert len(cat) == 13
    for lat, lng in centroides(cat).values():
        assert 19.0 <= lat <= 19.6 and -99.4 <= lng <= -98.9
