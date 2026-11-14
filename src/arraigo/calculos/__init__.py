"""Costo real de vivir y precio justo (spec 03). Todo determinista y sin LLM.

Contrato para la spec 05: `costo_real(inmueble, perfil, colonia)` y `precio_justo(inmueble, colonia)`.
"""
from arraigo.calculos.api import costo_real, precio_justo
from arraigo.calculos.compone_costo import calcular_costo_real
from arraigo.calculos.modelos import Componente, CostoReal, Hipoteca, PrecioJusto, TasaReferencia, Traslado
from arraigo.calculos.banda_precio import evaluar_precio_justo
from arraigo.calculos.supuestos import ConfigCalculos, TarifasSemovi, cargar_config, cargar_tarifas

__all__ = [
    "costo_real", "precio_justo", "calcular_costo_real", "evaluar_precio_justo",
    "Componente", "CostoReal", "Hipoteca", "PrecioJusto", "TasaReferencia", "Traslado",
    "ConfigCalculos", "TarifasSemovi", "cargar_config", "cargar_tarifas",
]
