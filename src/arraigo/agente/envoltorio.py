"""Envoltorio común de respuesta, avisos fijos y errores en español (R2)."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from pydantic import BaseModel, ValidationError

from arraigo.schemas.colonia import Dato
from arraigo.schemas.inmueble import Inmueble

AVISO_SINTETICO = "Este anuncio es de ejemplo (sintético), no es una oferta real."
AVISO_UBICACION = "La ubicación es aproximada (centro de la colonia), no la dirección del inmueble."
AVISO_HIPOTECA = "Estimación de mensualidad, no es asesoría hipotecaria."
AVISO_PENDIENTE_03 = "pendiente spec 03"


def aviso_sin_dato(campo: str, sujeto: str) -> str:
    return f"No hay dato de {campo} para {sujeto}."


class Fuente(BaseModel):
    descripcion: str
    fecha_dato: date | None = None


class Envoltorio(BaseModel):
    ok: bool = True
    datos: dict | list | None = None
    explicacion: str
    fuentes: list[Fuente] = []
    avisos: list[str] = []
    error: str | None = None  # solo si ok = False


def deduplicar(textos: Iterable[str]) -> list[str]:
    """Quita repetidos conservando el orden de aparición."""
    vistos: dict[str, None] = {}
    for t in textos:
        if t:
            vistos.setdefault(t, None)
    return list(vistos)


def deduplicar_fuentes(fuentes: Iterable[Fuente]) -> list[Fuente]:
    vistas: dict[tuple[str, date | None], Fuente] = {}
    for f in fuentes:
        vistas.setdefault((f.descripcion, f.fecha_dato), f)
    return list(vistas.values())


def fuente_de_dato(dato: Dato[Any], sujeto: str | None = None) -> Fuente | None:
    """Fuente de un `Dato` con valor; None si el dato está vacío."""
    if dato.valor is None or not dato.fuente:
        return None
    descripcion = f"{dato.fuente}, {sujeto}" if sujeto else dato.fuente
    return Fuente(descripcion=descripcion, fecha_dato=dato.fecha_dato)


def avisos_inmueble(inmueble: Inmueble) -> list[str]:
    """Avisos obligatorios de R2.2 y R2.3."""
    avisos = []
    if inmueble.fuente == "sintetico":
        avisos.append(AVISO_SINTETICO)
    if inmueble.ubicacion_aproximada:
        avisos.append(AVISO_UBICACION)
    return avisos


def inmueble_publico(inmueble: Inmueble) -> dict:
    """Inmueble listo para responder: sin `es_fraude_prueba` ni `url_origen` vacía (R6.2)."""
    datos = inmueble.model_dump(mode="json", exclude={"es_fraude_prueba"})
    if not datos.get("url_origen"):
        datos.pop("url_origen", None)
    return datos


def error(mensaje: str, datos: dict | list | None = None) -> Envoltorio:
    return Envoltorio(ok=False, datos=datos, explicacion=mensaje, error=mensaje)


_MOTIVOS = {
    "missing": "falta este campo",
    "int_parsing": "debe ser un número entero",
    "int_type": "debe ser un número entero",
    "float_parsing": "debe ser un número",
    "bool_parsing": "debe ser verdadero o falso",
    "string_type": "debe ser texto",
    "list_type": "debe ser una lista",
    "dict_type": "debe ser un objeto",
    "model_type": "debe ser un objeto",
    "extra_forbidden": "campo no permitido",
}


def _motivo(e: dict) -> str:
    tipo = e.get("type", "")
    ctx = e.get("ctx") or {}
    if tipo == "value_error":
        return str(ctx.get("error", e.get("msg", ""))).removeprefix("Value error, ")
    if tipo in _MOTIVOS:
        return _MOTIVOS[tipo]
    if tipo == "greater_than_equal":
        return f"debe ser mayor o igual a {ctx.get('ge')}"
    if tipo == "greater_than":
        return f"debe ser mayor que {ctx.get('gt')}"
    if tipo == "less_than_equal":
        return f"debe ser menor o igual a {ctx.get('le')}"
    if tipo == "less_than":
        return f"debe ser menor que {ctx.get('lt')}"
    if tipo == "literal_error":
        return f"valor no permitido; opciones: {ctx.get('expected')}"
    if tipo == "too_short":
        return f"debe tener al menos {ctx.get('min_length')} elemento(s)"
    if tipo == "too_long":
        return f"debe tener como máximo {ctx.get('max_length')} elemento(s)"
    return e.get("msg", "valor inválido")


def mensaje_validacion(exc: ValidationError, prefijo: str = "") -> str:
    """'campo: motivo' en español por cada error (R2.8)."""
    partes = []
    for e in exc.errors():
        loc = ".".join(str(p) for p in e.get("loc", ()) if p != "__root__")
        campo = ".".join(p for p in (prefijo, loc) if p)
        if not loc:
            # Errores de validadores de modelo: el mensaje ya dice el campo ("prioridades no puede...").
            motivo = _motivo(e)
            primero, _, resto = motivo.partition(" ")
            campo = primero if not prefijo else f"{prefijo}.{primero}"
            partes.append(f"{campo}: {resto}" if resto else f"{prefijo or 'entrada'}: {motivo}")
        else:
            partes.append(f"{campo}: {_motivo(e)}")
    return "; ".join(partes)


def error_validacion(exc: ValidationError, prefijo: str = "") -> Envoltorio:
    return error(f"Entrada inválida. {mensaje_validacion(exc, prefijo)}")
