"""Interfaz pública de la spec 03 para la spec 05: `costo_real(inmueble, perfil, colonia)` y `precio_justo(inmueble, colonia)`.

Cargan la configuración, las tarifas y la última tasa guardada de `data/raw/` (sin red) y llaman a las funciones puras.
Para refrescar la tasa desde Banxico usa `arraigo.pipeline.referencias.obtener_tasa_referencia()` y pásala en `tasa`.
"""
from __future__ import annotations

from arraigo.calculos.compone_costo import calcular_costo_real
from arraigo.calculos.modelos import CostoReal, PrecioJusto, TasaReferencia
from arraigo.calculos.banda_precio import evaluar_precio_justo
from arraigo.calculos.supuestos import (
    ConfigCalculos,
    TarifasSemovi,
    cargar_tasa_guardada,
    config_por_defecto,
    tarifas_por_defecto,
)
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble
from arraigo.schemas.perfil import Perfil


def costo_real(
    inmueble: Inmueble,
    perfil: Perfil,
    colonia: Colonia | None = None,
    *,
    config: ConfigCalculos | None = None,
    tarifas: TarifasSemovi | None = None,
    tasa: TasaReferencia | None = None,
) -> CostoReal:
    """Costo real mensual (con y sin tiempo valorizado), desglose, supuestos y avisos."""
    return calcular_costo_real(
        inmueble,
        perfil,
        colonia,
        config or config_por_defecto(),
        tarifas or tarifas_por_defecto(),
        tasa or cargar_tasa_guardada(),
    )


def precio_justo(inmueble: Inmueble, colonia: Colonia | None = None, *, config: ConfigCalculos | None = None) -> PrecioJusto:
    """Banda de precio (`sospechosamente_barato`, `justo`, `caro` o `no_evaluable`) contra la mediana de la colonia."""
    return evaluar_precio_justo(inmueble, colonia, config or config_por_defecto())
