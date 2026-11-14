"""Modelos del antifraude (spec 04)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from arraigo.antifraude.duplicados import IndiceDuplicados
from arraigo.schemas.colonia import Dato
from arraigo.schemas.inmueble import Operacion

RAIZ = Path(__file__).resolve().parents[3]
RUTA_CONFIG = RAIZ / "data" / "raw" / "antifraude_reglas.json"


class ConfigReglas(BaseModel):
    """Configuración versionada: pesos, umbrales, niveles y frases (R1.4)."""

    version: int
    umbral_alerta: int = 30
    niveles: dict[str, int] = {"medio": 30, "alto": 60}
    min_anuncios_mediana: int = 5
    reglas: dict[str, dict[str, Any]]

    def peso(self, regla: str) -> int:
        return int(self.reglas.get(regla, {}).get("peso", 0))

    def param(self, regla: str, clave: str, defecto: Any = None) -> Any:
        return self.reglas.get(regla, {}).get(clave, defecto)


def cargar_config(ruta: Path = RUTA_CONFIG) -> ConfigReglas:
    return ConfigReglas.model_validate(json.loads(Path(ruta).read_text(encoding="utf-8")))


class Senal(BaseModel):
    regla: str
    puntos: int = Field(ge=1)
    evidencia: str
    explicacion: str


class NoEvaluable(BaseModel):
    regla: str
    motivo: str


class ContextoAntifraude(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # (colonia normalizada, operacion) -> mediana de precio por m2
    medianas_m2: dict[tuple[str, Operacion], Dato[float]] = {}
    indice_duplicados: IndiceDuplicados = Field(default_factory=IndiceDuplicados)
    config: ConfigReglas


class ResultadoAntifraude(BaseModel):
    id: str
    score_riesgo: int = Field(ge=0, le=100)
    nivel: Literal["bajo", "medio", "alto"]
    senales: list[Senal]
    no_evaluables: list[str]
    resumen: str
    recomendacion: str
    fuente_referencia: str | None = None
    es_sintetico: bool = False
