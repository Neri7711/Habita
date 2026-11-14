"""Configuración de la spec 03: supuestos y tarifas SEMOVI cargados de `data/raw/`.

Falla al cargar si algún supuesto no trae fuente o fecha, o si alguna tarifa no trae URL ni vigencia (R2.8, R8.1).
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from arraigo.calculos.modelos import TasaReferencia

RAIZ = Path(__file__).resolve().parents[3]
RUTA_SUPUESTOS = RAIZ / "data" / "raw" / "calculos_supuestos.json"
RUTA_TARIFAS = RAIZ / "data" / "raw" / "tarifas_semovi.json"
RUTA_TASA = RAIZ / "data" / "raw" / "tasa_referencia.json"

MODOS_CALCULO = ("transporte_publico", "auto", "bici")


class _Seccion(BaseModel):
    fuente: str = Field(min_length=1)
    fecha_dato: date


class SeccionTraslado(_Seccion):
    factor_rodeo: dict[str, float]
    velocidad_kmh: dict[str, float]

    @field_validator("factor_rodeo", "velocidad_kmh")
    @classmethod
    def _todos_los_modos(cls, v: dict[str, float]) -> dict[str, float]:
        faltan = [m for m in MODOS_CALCULO if m not in v or v[m] <= 0]
        if faltan:
            raise ValueError(f"faltan valores positivos para los modos: {faltan}")
        return v


class Calendario(_Seccion):
    dias_laborales_mes: int = Field(gt=0)
    horas_laborales_dia: float = Field(gt=0)
    viajes_por_dia: int = Field(gt=0)


class Tramo(BaseModel):
    hasta_km: float | None
    pasajes: int = Field(gt=0)


class Pasajes(_Seccion):
    tramos: list[Tramo] = Field(min_length=1)

    def pasajes_para(self, distancia_ruta_km: float) -> int:
        for t in self.tramos:
            if t.hasta_km is None or distancia_ruta_km <= t.hasta_km:
                return t.pasajes
        return self.tramos[-1].pasajes


class TransportePublico(_Seccion):
    tarifa_por_defecto: str
    mapeo_estacion: dict[str, str]


class Auto(_Seccion):
    costo_por_km_mxn: float = Field(ge=0)
    nota: str


class Tiempo(_Seccion):
    factor_valor_tiempo: float = Field(ge=0)


class Servicios(_Seccion):
    base_mxn: float = Field(ge=0)
    por_recamara_mxn: float = Field(ge=0)
    desglose_pct: dict[str, float]


class Compra(_Seccion):
    mantenimiento_predial_anual_pct: float = Field(ge=0)
    plazo_anios: int = Field(gt=0)
    enganche_minimo_pct: float = Field(ge=0, le=1)
    spread_sobre_tiie_pp: float
    tasa_respaldo_anual_pct: float = Field(ge=0)
    serie_banxico: str
    pago_max_pct_ingreso: float = Field(gt=0, le=1)


class PrecioJustoCfg(_Seccion):
    umbral_sospechosamente_barato: float = Field(gt=0)
    umbral_caro: float = Field(gt=0)


class ConfigCalculos(BaseModel):
    version: int = 1
    traslado: SeccionTraslado
    calendario: Calendario
    pasajes: Pasajes
    transporte_publico: TransportePublico
    auto: Auto
    tiempo: Tiempo
    servicios: Servicios
    compra: Compra
    precio_justo: PrecioJustoCfg


class Tarifa(BaseModel):
    mxn: float = Field(ge=0)
    tipo_cobro: str
    url: str = Field(min_length=1)
    fecha_vigencia: date


class TarifasSemovi(BaseModel):
    version: int = 1
    nota: str = ""
    tarifas: dict[str, Tarifa]

    @field_validator("tarifas")
    @classmethod
    def _minimas(cls, v: dict[str, Tarifa]) -> dict[str, Tarifa]:
        obligatorias = ("metro", "metrobus", "trolebus", "tren_ligero", "rtp", "cablebus", "ecobici_anual")
        faltan = [t for t in obligatorias if t not in v]
        if faltan:
            raise ValueError(f"faltan tarifas obligatorias: {faltan}")
        return v


def _leer_json(ruta: Path) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def cargar_config(ruta: Path = RUTA_SUPUESTOS) -> ConfigCalculos:
    return ConfigCalculos.model_validate(_leer_json(ruta))


def cargar_tarifas(ruta: Path = RUTA_TARIFAS) -> TarifasSemovi:
    return TarifasSemovi.model_validate(_leer_json(ruta))


def cargar_tasa_guardada(ruta: Path = RUTA_TASA) -> TasaReferencia | None:
    """Última tasa guardada por `pipeline.referencias`; None si el archivo no existe."""
    if not Path(ruta).exists():
        return None
    return TasaReferencia.model_validate(_leer_json(ruta))


def tasa_respaldo(config: ConfigCalculos) -> TasaReferencia:
    """Tasa de la tabla de supuestos, para cuando no hay dato de Banxico (R5.4)."""
    return TasaReferencia(
        tasa_pct=config.compra.tasa_respaldo_anual_pct,
        fecha=config.compra.fecha_dato,
        fuente="respaldo",
        es_respaldo=True,
    )


@lru_cache(maxsize=1)
def config_por_defecto() -> ConfigCalculos:
    return cargar_config()


@lru_cache(maxsize=1)
def tarifas_por_defecto() -> TarifasSemovi:
    return cargar_tarifas()
