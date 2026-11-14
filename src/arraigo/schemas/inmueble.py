"""Esquema de inmueble (R1)."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, ValidationInfo, model_validator


class Operacion(str, Enum):
    renta = "renta"
    venta = "venta"


class Requisito(str, Enum):
    aval = "aval"
    poliza = "poliza"
    deposito_extra = "deposito_extra"
    ninguno = "ninguno"


class Inmueble(BaseModel):
    id: str = Field(min_length=1)
    operacion: Operacion
    precio_mxn: int = Field(gt=0)
    colonia: str = Field(min_length=1)
    alcaldia: str = Field(min_length=1)
    lat: float | None = Field(default=None, ge=19.0, le=19.6)
    lng: float | None = Field(default=None, ge=-99.4, le=-98.9)
    ubicacion_aproximada: bool = False
    m2: float | None = Field(default=None, ge=10, le=1000)
    recamaras: int = Field(ge=0, le=10)
    banos: float = Field(ge=0.5, le=10)
    estacionamiento: int = Field(default=0, ge=0, le=10)
    acepta_mascotas: bool | None = None
    amueblado: bool | None = None
    requisitos: list[Requisito] = []
    descripcion: str = ""
    fuente: str = Field(min_length=1)
    fecha_captura: date
    url_origen: HttpUrl | None = None
    es_fraude_prueba: bool = False

    @model_validator(mode="after")
    def _completar_ubicacion(self, info: ValidationInfo) -> Inmueble:
        """R1.2: sin lat/lng se usa el centroide de la colonia (context={"centroides": {colonia: (lat, lng)}})."""
        if self.lat is None or self.lng is None:
            centroide = ((info.context or {}).get("centroides") or {}).get(self.colonia)
            if centroide:
                self.lat, self.lng = centroide
            self.ubicacion_aproximada = True
        return self
