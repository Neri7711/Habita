"""Evalúa el antifraude contra es_fraude_prueba. Uso: uv run python scripts/evaluar_antifraude.py"""
import subprocess
import sys
from pathlib import Path

from arraigo.antifraude.evaluacion import ejecutar
from arraigo.antifraude.modelos import RAIZ

if not (RAIZ / "data" / "processed" / "inmuebles.json").exists():
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "cargar_dataset.py")], check=True)

rep = ejecutar()
for nombre, m in rep["metricas"].items():
    print(f"{nombre:11s} n={m['n']:4d} fraudes={m['fraudes']:3d} VP={m['vp']} FP={m['fp']} FN={m['fn']} VN={m['vn']} "
          f"precision={m['precision']} recall={m['recall']}")
print("Meta (recall>=0.85, precision>=0.80):", "SE CUMPLE" if rep["metas"]["cumple"] else "NO SE CUMPLE")
print(f"Reporte: {Path('data/processed/reporte_antifraude.md')}")
