"""Utilidades de texto para las reglas (funciones puras)."""
from __future__ import annotations

import re
import unicodedata

_TELEFONO = re.compile(r"\+\d{1,3}(?:[\s-]?\d{2,4}){2,4}")


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos."""
    sin_acentos = unicodedata.normalize("NFKD", texto or "")
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return sin_acentos.lower().strip()


def buscar_frase(texto_normalizado: str, patrones: list[str]) -> str | None:
    """Devuelve el primer fragmento que coincide con algún patrón, o None."""
    for patron in patrones:
        m = re.search(patron, texto_normalizado)
        if m:
            return m.group(0).strip()
    return None


def extraer_telefonos(texto: str) -> list[str]:
    """Teléfonos con prefijo internacional (+NN ...)."""
    return [m.group(0).strip() for m in _TELEFONO.finditer(texto or "")]


def prefijo_telefono(telefono: str) -> str:
    """Dígitos del prefijo tal como se escribió: '+44 7700...' -> '44...' (solo dígitos iniciales)."""
    return re.sub(r"\D", "", telefono)


def ocultar_telefono(telefono: str, visibles_ocultos: int = 4) -> str:
    """Reemplaza los últimos dígitos por '*' para no exponer el contacto."""
    letras = list(telefono)
    pendientes = visibles_ocultos
    for i in range(len(letras) - 1, -1, -1):
        if pendientes == 0:
            break
        if letras[i].isdigit():
            letras[i] = "*"
            pendientes -= 1
    return "".join(letras)


def palabras(texto_normalizado: str) -> list[str]:
    return re.findall(r"\w+", texto_normalizado)
