"""Similitud entre descripciones: Jaccard sobre shingles de 3 palabras."""
from __future__ import annotations

from dataclasses import dataclass

from arraigo.antifraude.texto import normalizar, palabras


def shingles(texto: str, n: int = 3) -> frozenset[tuple[str, ...]]:
    p = palabras(normalizar(texto))
    if len(p) < n:
        return frozenset([tuple(p)]) if p else frozenset()
    return frozenset(tuple(p[i : i + n]) for i in range(len(p) - n + 1))


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class _Entrada:
    id: str
    colonia: str
    precio: int
    shingles: frozenset
    n_palabras: int


class IndiceDuplicados:
    """Descripciones de los anuncios conocidos."""

    def __init__(self) -> None:
        self._entradas: list[_Entrada] = []

    def __len__(self) -> int:
        return len(self._entradas)

    def agregar(self, id: str, colonia: str, precio: int, descripcion: str) -> None:
        self._entradas.append(
            _Entrada(
                id=id,
                colonia=normalizar(colonia),
                precio=precio,
                shingles=shingles(descripcion),
                n_palabras=len(palabras(normalizar(descripcion))),
            )
        )

    def buscar(
        self,
        id: str,
        colonia: str,
        precio: int,
        descripcion: str,
        jaccard_min: float,
        min_palabras: int,
        dif_precio_max: float,
    ) -> tuple[str, float] | None:
        """Otro anuncio casi igual pero de otra colonia o con otro precio (>dif_precio_max)."""
        s = shingles(descripcion)
        if len(palabras(normalizar(descripcion))) < min_palabras:
            return None
        col = normalizar(colonia)
        mejor: tuple[str, float] | None = None
        for e in self._entradas:
            if e.id == id or e.n_palabras < min_palabras:
                continue
            sim = jaccard(s, e.shingles)
            if sim < jaccard_min:
                continue
            otra_colonia = e.colonia != col
            otro_precio = abs(precio - e.precio) / max(e.precio, 1) > dif_precio_max
            if (otra_colonia or otro_precio) and (mejor is None or sim > mejor[1]):
                mejor = (e.id, sim)
        return mejor
