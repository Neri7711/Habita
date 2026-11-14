"""Esquemas Pydantic (spec 01)."""

from arraigo.schemas.colonia import Colonia, Dato, Estacion, NivelRiesgo, Punto, PuntoComunidad
from arraigo.schemas.inmueble import Inmueble, Operacion, Requisito
from arraigo.schemas.perfil import Perfil, Ubicacion

__all__ = [
    "Colonia", "Dato", "Estacion", "NivelRiesgo", "Punto", "PuntoComunidad",
    "Inmueble", "Operacion", "Requisito",
    "Perfil", "Ubicacion",
]
