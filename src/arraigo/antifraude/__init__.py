"""Antifraude (spec 04): reglas deterministas + score explicable."""
from arraigo.antifraude.modelos import (
    ConfigReglas,
    ContextoAntifraude,
    ResultadoAntifraude,
    Senal,
    cargar_config,
)
from arraigo.antifraude.score import construir_contexto, evaluar_anuncio, evaluar_anuncio_nuevo

__all__ = [
    "ConfigReglas", "ContextoAntifraude", "ResultadoAntifraude", "Senal", "cargar_config",
    "construir_contexto", "evaluar_anuncio", "evaluar_anuncio_nuevo",
]
