from arraigo.antifraude.duplicados import IndiceDuplicados, jaccard, shingles


def test_jaccard_identicos_casi_y_distintos():
    a = "departamento amplio con balcon cerca del metro y comercios listo para mudarse"
    casi = a + " hoy"
    otro = "casa con jardin grande lejos del centro sin transporte publico cercano alguno"
    assert jaccard(shingles(a), shingles(a)) == 1.0
    assert 0.8 <= jaccard(shingles(a), shingles(casi)) < 1.0
    assert jaccard(shingles(a), shingles(otro)) < 0.2


def test_jaccard_vacio():
    assert jaccard(shingles(""), shingles("hola")) == 0.0


def test_indice_ignora_el_mismo_id():
    t = "departamento amplio con balcon cerca del metro y comercios listo para mudarse"
    idx = IndiceDuplicados()
    idx.agregar("a", "Roma", 1000, t)
    assert idx.buscar("a", "Juárez", 1000, t, 0.8, 6, 0.1) is None
    assert idx.buscar("b", "Juárez", 1000, t, 0.8, 6, 0.1) is not None
