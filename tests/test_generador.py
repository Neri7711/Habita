from collections import Counter

from arraigo.pipeline.colonias import cargar_catalogo
from arraigo.pipeline.sinteticos import COLUMNAS, generar


def test_generador_reproducible_y_completo():
    cat = cargar_catalogo()
    a, b = generar(cat, seed=42), generar(cat, seed=42)
    assert a == b and len(a) == 300
    assert list(a[0]) == COLUMNAS
    assert sum(f["es_fraude_prueba"] == "true" for f in a) >= 20
    ops = Counter((f["colonia"], f["operacion"]) for f in a)
    assert all(ops[(c["colonia"], op)] > 0 for c in cat.values() for op in ("renta", "venta"))
    assert all(f["fuente"] == "sintetico" and f["url_origen"] == "" for f in a)
