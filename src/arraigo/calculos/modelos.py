"""Modelos de resultado de la spec 03 (costo real y precio justo)."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TasaReferencia(BaseModel):
    """Tasa de referencia (TIIE a 28 días) que recibe el cálculo como parámetro."""

    tasa_pct: float
    fecha: date
    fuente: str
    es_respaldo: bool = False


class Traslado(BaseModel):
    distancia_recta_km: float
    distancia_ruta_km: float
    minutos_ida: int
    modo_usado: str  # "transporte_publico" si el perfil dijo "mixto"
    excede_tiempo_max: bool
    avisos: list[str] = Field(default_factory=list)


class Componente(BaseModel):
    monto_mxn: int | None  # None = no calculable
    fuente: str
    fecha_dato: date
    supuestos: list[str] = Field(default_factory=list)
    motivo_no_calculable: str | None = None
    desglose: dict[str, int] = Field(default_factory=dict)


class Hipoteca(BaseModel):
    mensualidad_mxn: int
    enganche_mxn: int
    monto_financiado_mxn: int
    tasa_anual_pct: float  # TIIE + spread
    tasa_referencia_pct: float  # TIIE sola
    plazo_anios: int
    fuente_tasa: str
    fecha_tasa: date
    es_tasa_respaldo: bool = False
    avisos: list[str] = Field(default_factory=list)


class PrecioJusto(BaseModel):
    banda: Literal["sospechosamente_barato", "justo", "caro", "no_evaluable"]
    precio_m2: float | None = None
    mediana_m2: float | None = None
    razon: float | None = None
    diferencia_pct: float | None = None  # (razon - 1) * 100
    n_anuncios_mediana: int | None = None
    fuente_referencia: str | None = None
    es_sintetico: bool = False
    explicacion: str
    motivo_no_evaluable: str | None = None


class CostoReal(BaseModel):
    inmueble_id: str
    operacion: Literal["renta", "venta"]
    vivienda: Componente  # renta o mensualidad de compra
    transporte: Componente
    servicios: Componente
    tiempo_valorizado: Componente
    horas_traslado_mes: float | None
    costo_monetario_mxn: int | None  # vivienda + transporte + servicios
    costo_real_mxn: int | None  # monetario + tiempo valorizado
    pct_ingreso_monetario: float | None
    pct_ingreso_real: float | None
    traslado: Traslado | None
    hipoteca: Hipoteca | None
    enganche_inicial_mxn: int | None  # solo compra; no está en el costo mensual
    excede_presupuesto: bool
    pago_excede_ingreso: bool
    precio_justo: PrecioJusto
    es_sintetico: bool
    avisos: list[str] = Field(default_factory=list)
    resumen: str
