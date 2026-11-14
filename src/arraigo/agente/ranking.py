"""Filtros duros, criterios normalizados 0-1, pesos por posición y puntuación (R3.2-3.8, R3.11).

Funciones puras: reciben los valores crudos ya calculados (costo y minutos vienen de la spec 03).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble, Operacion, Requisito
from arraigo.schemas.perfil import Perfil

PESOS_BASE = (0.35, 0.25, 0.20, 0.12, 0.08)
NEUTRO = 0.5
CRITERIOS = ("precio", "traslado", "seguridad", "comunidad", "espacio")
NOMBRE_CRITERIO = {
    "precio": "costo mensual",
    "traslado": "tiempo de traslado",
    "seguridad": "índice de delitos",
    "comunidad": "lugares de comunidad y estaciones",
    "espacio": "metros cuadrados",
}

# Orden en que se aplican los filtros duros; el conteo se atribuye al primero que falla.
FILTROS = ("operacion", "presupuesto", "recamaras", "mascotas", "aval")


def pesos(prioridades: list[str]) -> dict[str, float]:
    """Primeros n pesos base reescalados para sumar 1; la primera prioridad pesa más (R3.6)."""
    base = PESOS_BASE[: len(prioridades)]
    total = sum(base)
    return {p: b / total for p, b in zip(prioridades, base)}


def operaciones_de(perfil: Perfil) -> set[Operacion]:
    return {
        "renta": {Operacion.renta},
        "compra": {Operacion.venta},
        "ambas": {Operacion.renta, Operacion.venta},
    }[perfil.operacion_deseada]


def primer_filtro_que_falla(inmueble: Inmueble, perfil: Perfil) -> str | None:
    """Nombre del primer filtro duro que excluye al inmueble (R3.2, R3.3) o None si pasa todos."""
    if inmueble.operacion not in operaciones_de(perfil):
        return "operacion"
    if inmueble.precio_mxn > perfil.presupuesto_max_mxn:
        return "presupuesto"
    if inmueble.recamaras < perfil.recamaras_min:
        return "recamaras"
    if perfil.mascotas and inmueble.acepta_mascotas is False:
        return "mascotas"
    if not perfil.tiene_aval and inmueble.operacion == Operacion.renta and Requisito.aval in inmueble.requisitos:
        return "aval"
    return None


def filtros_duros(inmuebles: list[Inmueble], perfil: Perfil) -> tuple[list[Inmueble], dict[str, int]]:
    conteo = {f: 0 for f in FILTROS}
    pasan = []
    for i in inmuebles:
        falla = primer_filtro_que_falla(i, perfil)
        if falla:
            conteo[falla] += 1
        else:
            pasan.append(i)
    return pasan, conteo


def normalizar_min_max(valores: dict[str, float | None], invertir: bool = False) -> dict[str, float | None]:
    """Escala 0-1; con `invertir` el menor vale 1. Si max == min, todos 0.5. Los None se quedan None."""
    presentes = [v for v in valores.values() if v is not None]
    if not presentes:
        return dict(valores)
    lo, hi = min(presentes), max(presentes)
    salida: dict[str, float | None] = {}
    for k, v in valores.items():
        if v is None:
            salida[k] = None
        elif hi == lo:
            salida[k] = NEUTRO
        else:
            x = (v - lo) / (hi - lo)
            salida[k] = 1 - x if invertir else x
    return salida


def medida_seguridad(colonia: Colonia | None) -> float | None:
    return colonia.indice_delitos.valor if colonia else None


def medida_comunidad(colonia: Colonia | None) -> float | None:
    """`len(puntos_comunidad) + len(estaciones)`; None si faltan los dos."""
    if colonia is None:
        return None
    puntos = colonia.puntos_comunidad.valor
    estaciones = colonia.estaciones_transporte_cercanas.valor
    if puntos is None and estaciones is None:
        return None
    return float(len(puntos or []) + len(estaciones or []))


@dataclass
class Candidato:
    """Valores crudos de un anuncio que ya pasó los filtros."""

    inmueble: Inmueble
    colonia: Colonia | None
    costo_mensual: float | None  # costo real total (spec 03) o, si no hay, precio publicado
    minutos: float | None


@dataclass
class Puntuado:
    candidato: Candidato
    puntuacion: float
    desglose: dict[str, float]  # puntos que aporta cada prioridad
    criterios: dict[str, float]  # valor 0-1 usado (0.5 si faltó)
    faltantes: list[str] = field(default_factory=list)  # criterios sin dato

    @property
    def id(self) -> str:
        return self.candidato.inmueble.id


def puntuar(candidatos: list[Candidato], prioridades: list[str], colonias: list[Colonia]) -> list[Puntuado]:
    """Puntuación 0-100 = 100 × Σ peso × criterio; orden (-puntuación, id) (R3.6-3.8, R3.11).

    `precio`, `traslado` y `espacio` se normalizan entre candidatos de la misma operación;
    `seguridad` y `comunidad`, sobre todas las colonias, para que signifiquen lo mismo en cualquier búsqueda.
    """
    w = pesos(prioridades)
    norm: dict[str, dict[str, float | None]] = {c: {} for c in CRITERIOS}

    for op in {c.inmueble.operacion for c in candidatos}:
        grupo = [c for c in candidatos if c.inmueble.operacion == op]
        norm["precio"].update(normalizar_min_max({c.inmueble.id: c.costo_mensual for c in grupo}, invertir=True))
        norm["traslado"].update(normalizar_min_max({c.inmueble.id: c.minutos for c in grupo}, invertir=True))
        norm["espacio"].update(normalizar_min_max({c.inmueble.id: c.inmueble.m2 for c in grupo}))

    seg_col = normalizar_min_max({c.nombre: medida_seguridad(c) for c in colonias}, invertir=True)
    com_col = normalizar_min_max({c.nombre: medida_comunidad(c) for c in colonias})
    for c in candidatos:
        nombre = c.colonia.nombre if c.colonia else None
        norm["seguridad"][c.inmueble.id] = seg_col.get(nombre) if nombre else None
        norm["comunidad"][c.inmueble.id] = com_col.get(nombre) if nombre else None

    resultado = []
    for c in candidatos:
        criterios, desglose, faltantes = {}, {}, []
        for p, peso in w.items():
            v = norm[p].get(c.inmueble.id)
            if v is None:
                v = NEUTRO
                faltantes.append(p)
            criterios[p] = v
            desglose[p] = round(100 * peso * v, 2)
        puntuacion = round(sum(100 * w[p] * criterios[p] for p in w), 2)
        resultado.append(Puntuado(c, puntuacion, desglose, criterios, faltantes))
    resultado.sort(key=lambda r: (-r.puntuacion, r.id))
    return resultado


def fraccion_peor(valor: float, otros: list[float], menor_es_mejor: bool) -> float:
    """Fracción de los otros valores que quedan peor que `valor` (respaldo numérico de 'más que la mayoría')."""
    if not otros:
        return 0.0
    peores = sum(1 for o in otros if (o > valor if menor_es_mejor else o < valor))
    return peores / len(otros)
