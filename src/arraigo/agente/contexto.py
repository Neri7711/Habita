"""Contexto del agente: datos en memoria cargados una sola vez (R1.4, R1.5)."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from arraigo.antifraude import ConfigReglas, ContextoAntifraude, ResultadoAntifraude, cargar_config
from arraigo.antifraude.score import construir_contexto, evaluar_anuncio
from arraigo.antifraude.texto import normalizar
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble

RAIZ = Path(__file__).resolve().parents[3]
RUTA_PROCESSED = RAIZ / "data" / "processed"
COMANDO_GENERAR = "uv run python scripts/cargar_dataset.py"


class ErrorDatos(Exception):
    """Faltan o están mal los archivos de `data/processed/`."""


class ContextoAgente(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    inmuebles: dict[str, Inmueble]  # por id
    colonias: dict[str, Colonia]  # por nombre normalizado
    nombres_colonia: dict[str, str]  # normalizado -> nombre oficial
    antifraude: ContextoAntifraude
    resultados_antifraude: dict[str, ResultadoAntifraude]  # precalculado; no usa es_fraude_prueba
    generado_en: date

    def colonia_de(self, inmueble: Inmueble) -> Colonia | None:
        return self.colonias.get(normalizar_colonia(inmueble.colonia))


def normalizar_colonia(nombre: str) -> str:
    """Minúsculas, sin acentos, sin el prefijo "col."/"colonia" y con espacios simples."""
    texto = normalizar(nombre)
    texto = re.sub(r"^(col\.?|colonia)\s+", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def construir_contexto_agente(
    inmuebles: list[Inmueble],
    colonias: list[Colonia],
    config: ConfigReglas | None = None,
    generado_en: date | None = None,
) -> ContextoAgente:
    """Arma el contexto y precalcula el score de riesgo de todos los anuncios."""
    antifraude = construir_contexto(inmuebles, colonias, config or cargar_config())
    return ContextoAgente(
        inmuebles={i.id: i for i in inmuebles},
        colonias={normalizar_colonia(c.nombre): c for c in colonias},
        nombres_colonia={normalizar_colonia(c.nombre): c.nombre for c in colonias},
        antifraude=antifraude,
        resultados_antifraude={i.id: evaluar_anuncio(i, antifraude) for i in inmuebles},
        generado_en=generado_en or date.today(),
    )


def _leer_lista(ruta: Path) -> list:
    if not ruta.exists():
        raise ErrorDatos(f"Falta el archivo {ruta.name} en data/processed/. Genéralo con: {COMANDO_GENERAR}")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ErrorDatos(f"{ruta.name} no es JSON válido ({exc}). Vuelve a generarlo con: {COMANDO_GENERAR}") from exc
    if not isinstance(datos, list):
        raise ErrorDatos(f"{ruta.name} debe ser una lista. Vuelve a generarlo con: {COMANDO_GENERAR}")
    return datos


def cargar_contexto(ruta_processed: Path = RUTA_PROCESSED, config: ConfigReglas | None = None) -> ContextoAgente:
    """Lee `inmuebles.json` y `colonias.json`. Solo lectura: no escribe en disco."""
    ruta_processed = Path(ruta_processed)
    crudos_inm = _leer_lista(ruta_processed / "inmuebles.json")
    crudos_col = _leer_lista(ruta_processed / "colonias.json")
    try:
        inmuebles = [Inmueble.model_validate(d) for d in crudos_inm]
        colonias = [Colonia.model_validate(d) for d in crudos_col]
    except ValidationError as exc:
        raise ErrorDatos(f"Los datos procesados no pasan el esquema ({exc.error_count()} errores). "
                         f"Vuelve a generarlos con: {COMANDO_GENERAR}") from exc
    return construir_contexto_agente(inmuebles, colonias, config)
