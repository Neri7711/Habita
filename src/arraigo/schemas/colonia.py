"""Esquema de colonia (R3). En la spec 01 solo se llenan centroide y medianas; el resto es de la spec 02."""

from __future__ import annotations

from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


class Dato(BaseModel, Generic[T]):
    """Valor con procedencia (R3.2): todo valor no nulo lleva fuente y fecha_dato."""

    valor: T | None = None
    fuente: str | None = None
    fecha_dato: date | None = None

    @model_validator(mode="after")
    def _procedencia(self) -> Dato[T]:
        if self.valor is not None and (not self.fuente or self.fecha_dato is None):
            raise ValueError("un dato con valor necesita fuente y fecha_dato")
        return self


class Punto(BaseModel):
    lat: float
    lng: float


class Estacion(BaseModel):
    nombre: str
    tipo: str  # metro, metrobus, ecobici, ...
    punto: Punto
    distancia_m: float | None = None


class NivelRiesgo(BaseModel):
    sismico: str | None = None
    inundacion: str | None = None


class PuntoComunidad(BaseModel):
    nombre: str
    tipo: str  # mercado, parque, centro_cultural, ...
    punto: Punto


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
