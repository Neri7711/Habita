"""Esquema de colonia (R3). En la spec 01 solo se llenan centroide y medianas; el resto es de la spec 02.

Spec 02 (tarea 1.1): se amplía sin romper el contrato de la spec 01, que ya usan las specs 03 y 05.
`indice_delitos` e `indicador_presion_gentrificacion` siguen siendo `Dato[float]` y `puntos_comunidad` sigue
siendo una lista; los datos crudos van en campos hermanos (`*_detalle`, `comercio_local`), como indica la
nota de la sección "Modelos" de .kiro/specs/02-enriquecimiento-colonias/design.md.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class Dato(BaseModel, Generic[T]):
    """Valor con procedencia (R3.2): todo valor no nulo lleva fuente y fecha_dato."""

    valor: T | None = None
    fuente: str | None = None
    fecha_dato: date | None = None
    explicacion: str | None = None  # texto en lenguaje simple para el agente (spec 02)

    @model_validator(mode="after")
    def _procedencia(self) -> Dato[T]:
        if self.valor is not None and (not self.fuente or self.fecha_dato is None):
            raise ValueError("un dato con valor necesita fuente y fecha_dato")
        return self


class Punto(BaseModel):
    lat: float
    lng: float


class Modo(str, Enum):
    metro = "metro"
    metrobus = "metrobus"
    tren_ligero = "tren_ligero"
    cablebus = "cablebus"
    trolebus = "trolebus"
    ecobici = "ecobici"


class Estacion(BaseModel):
    nombre: str
    tipo: Modo  # modo de transporte; se llama `tipo` por contrato de la spec 01
    punto: Punto
    distancia_m: float | None = None


class Nivel(str, Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"


class NivelRiesgo(BaseModel):
    sismico: Nivel | None = None
    inundacion: Nivel | None = None
    clase_sismico: str | None = None  # clase de mayor área, p. ej. "Zona III (lacustre)"
    clase_inundacion: str | None = None
    capa_sismico: str | None = None  # nombre de la capa del Atlas usada
    capa_inundacion: str | None = None


class CategoriaComunidad(str, Enum):
    mercado = "mercado"
    parque = "parque"
    centro_cultural = "centro_cultural"


class PuntoComunidad(BaseModel):
    nombre: str | None = None  # OSM no siempre trae nombre
    tipo: CategoriaComunidad
    punto: Punto
    distancia_m: float | None = None


class ComercioLocal(BaseModel):
    """Resumen DENUE: conteos por tipo, sin nombres ni direcciones de negocios."""

    radio_m: int = Field(gt=0)
    total_negocios: int = Field(ge=0)
    por_tipo: dict[str, int] = Field(default_factory=dict)


class DetalleDelitos(BaseModel):
    delitos_12m: int = Field(ge=0)
    tasa: float | None = None
    base: str  # "por_1000_hab" o "por_km2", igual para todas las colonias


class PresionGentrificacion(BaseModel):
    """Heurística transparente, no medición validada (R5.9)."""

    valor: float = Field(ge=0, le=1)
    componentes: dict[str, float | None]  # densidad_airbnb, cambio_educacion, cambio_poblacion (0-1)
    componentes_faltantes: list[str] = Field(default_factory=list)
    crudos: dict[str, float | None] = Field(default_factory=dict)
    es_heuristica: bool = True


class Colonia(BaseModel):
    nombre: str = Field(min_length=1)
    alcaldia: str = Field(min_length=1)
    centroide: Dato[Punto] = Dato[Punto]()
    precio_m2_renta_mediana: Dato[float] = Dato[float]()
    precio_m2_venta_mediana: Dato[float] = Dato[float]()
    indice_delitos: Dato[float] = Dato[float]()
    estaciones_transporte_cercanas: Dato[list[Estacion]] = Dato[list[Estacion]]()
    nivel_riesgo: Dato[NivelRiesgo] = Dato[NivelRiesgo]()
    indicador_presion_gentrificacion: Dato[float] = Dato[float]()
    puntos_comunidad: Dato[list[PuntoComunidad]] = Dato[list[PuntoComunidad]]()
    # Campos hermanos de la spec 02 (detalle de los anteriores)
    indice_delitos_detalle: Dato[DetalleDelitos] = Dato[DetalleDelitos]()
    presion_gentrificacion_detalle: Dato[PresionGentrificacion] = Dato[PresionGentrificacion]()
    comercio_local: Dato[ComercioLocal] = Dato[ComercioLocal]()  # null si no hubo INEGI_TOKEN
