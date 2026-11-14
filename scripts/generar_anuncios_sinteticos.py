"""Genera data/raw/anuncios_sinteticos.csv. Uso: uv run python scripts/generar_anuncios_sinteticos.py --seed 42"""

import argparse
from pathlib import Path

from arraigo.pipeline.colonias import RAIZ, cargar_catalogo
from arraigo.pipeline.sinteticos import escribir_csv, generar, medianas_reales

p = argparse.ArgumentParser()
p.add_argument("--seed", type=int, default=42)
p.add_argument("--n", type=int, default=300)
p.add_argument("--salida", type=Path, default=RAIZ / "data" / "raw" / "anuncios_sinteticos.csv")
args = p.parse_args()

reales = medianas_reales(RAIZ / "data" / "raw" / "anuncios_reales.csv")
filas = generar(cargar_catalogo(), reales, n=args.n, seed=args.seed)
escribir_csv(filas, args.salida)
print(f"{len(filas)} anuncios -> {args.salida} (medianas reales: {len(reales)} grupos; resto PROVISIONAL)")
