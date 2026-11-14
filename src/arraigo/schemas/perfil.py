"""Esquema de perfil de usuario (R2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Prioridad = Literal["precio", "traslado", "seguridad", "comunidad", "espacio"]


class Ubicacion(BaseModel):
    # Zona metropolitana, más amplia que CDMX.
    lat: float = Field(ge=18.9, le=20.0)
    lng: float = Field(ge=-99.6, le=-98.6)
    direccion: str = ""


class Perfil(BaseModel):
    operacion_deseada: Literal["renta", "compra", "ambas"]
    presupuesto_max_mxn: int = Field(ge=1_000, le=50_000_000)
    ingreso_mensual_mxn: int = Field(ge=1_000, le=2_000_000)
    destino_trabajo: Ubicacion
    modo_transporte: Literal["transporte_publico", "auto", "bici", "mixto"]
    tiempo_max_traslado_min: int = Field(ge=5, le=180)
    recamaras_min: int = Field(default=0, ge=0, le=6)
    mascotas: bool = False
    tiene_aval: bool = False
    enganche_disponible_mxn: int | None = Field(default=None, ge=0)
    prioridades: list[Prioridad] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def _reglas(self) -> Perfil:
        if self.operacion_deseada in ("compra", "ambas") and self.enganche_disponible_mxn is None:
            raise ValueError("enganche_disponible_mxn es obligatorio si la operación incluye compra")
        if len(set(self.prioridades)) != len(self.prioridades):
            raise ValueError("prioridades no puede tener repetidos")
        return self
