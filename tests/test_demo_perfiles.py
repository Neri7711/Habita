import json
from pathlib import Path

import pytest

from arraigo.schemas.perfil import Perfil

RAIZ = Path(__file__).resolve().parents[1]
RUTA = RAIZ / "data" / "raw" / "demo_perfiles.json"
PROCESSED = RAIZ / "data" / "processed"


def _perfiles() -> list[Perfil]:
    return [Perfil.model_validate(p) for p in json.loads(RUTA.read_text(encoding="utf-8"))]


def test_tres_perfiles_validos():
    perfiles = _perfiles()
    assert len(perfiles) == 3
    ana, familia, diego = perfiles
    assert ana.operacion_deseada == "renta" and ana.prioridades[0] == "precio"
    assert familia.operacion_deseada == "compra" and familia.prioridades[:2] == ["seguridad", "comunidad"]
    assert diego.prioridades[0] == "comunidad"


@pytest.mark.skipif(not (PROCESSED / "inmuebles.json").exists() or not (PROCESSED / "colonias.json").exists(),
                    reason="sin data/processed; genera con uv run python scripts/cargar_dataset.py")
def test_cada_perfil_tiene_resultados_con_dataset_real():
    from arraigo.agente.contexto import cargar_contexto
    from arraigo.agente.herramientas import buscar_inmuebles

    ctx = cargar_contexto(PROCESSED)
    for perfil in _perfiles():
        env = buscar_inmuebles(ctx, perfil)
        assert env.ok, env.error
        assert len(env.datos["resultados"]) >= 1, env.explicacion
