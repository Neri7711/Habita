import pytest

from arraigo.antifraude.evaluacion import (
    META_PRECISION,
    META_RECALL,
    cargar_colonias,
    cargar_inmuebles,
    construir_reporte,
    evaluar_dataset,
    matriz_confusion,
    reporte_a_markdown,
)
from arraigo.antifraude.modelos import RAIZ, cargar_config
from arraigo.antifraude.score import construir_contexto

PROCESADO = RAIZ / "data" / "processed"


def test_matriz_con_datos_a_mano():
    pares = [(True, 80), (True, 20), (False, 40), (False, 10), (False, 5)]
    m = matriz_confusion(pares, 30)
    assert (m["vp"], m["fp"], m["fn"], m["vn"]) == (1, 1, 1, 2)
    assert m["precision"] == 0.5 and m["recall"] == 0.5


def test_denominador_cero_es_null():
    m = matriz_confusion([(False, 0)], 30)
    assert m["precision"] is None and m["recall"] is None


@pytest.fixture(scope="module")
def datos():
    ruta = PROCESADO / "inmuebles.json"
    if not ruta.exists():
        pytest.skip("falta data/processed/inmuebles.json (uv run python scripts/cargar_dataset.py)")
    inmuebles = cargar_inmuebles(ruta)
    config = cargar_config()
    ctx = construir_contexto(inmuebles, cargar_colonias(PROCESADO / "colonias.json"), config)
    return inmuebles, ctx, config


def test_metas_sobre_el_dataset(datos):
    inmuebles, ctx, config = datos
    m = construir_reporte(inmuebles, evaluar_dataset(inmuebles, ctx), config)["metricas"]["todos"]
    assert m["recall"] >= META_RECALL
    assert m["precision"] >= META_PRECISION


def test_es_fraude_prueba_no_afecta_el_score(datos):
    inmuebles, ctx, _ = datos
    base = evaluar_dataset(inmuebles, ctx)
    invertidos = [i.model_copy(update={"es_fraude_prueba": not i.es_fraude_prueba}) for i in inmuebles]
    otro = evaluar_dataset(invertidos, ctx)
    assert {k: v.score_riesgo for k, v in base.items()} == {k: v.score_riesgo for k, v in otro.items()}


def test_reporte_markdown_incluye_advertencias(datos):
    inmuebles, ctx, config = datos
    md = reporte_a_markdown(construir_reporte(inmuebles, evaluar_dataset(inmuebles, ctx), config))
    assert "optimista" in md and "Falsos positivos" in md and "evaluar_anuncio" in md
