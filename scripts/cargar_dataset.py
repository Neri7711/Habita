"""Corre el pipeline de la spec 01: colonias → validar anuncios → colonias.json → reporte.
Uso: uv run python scripts/cargar_dataset.py
"""

from arraigo.pipeline.cargar import construir_colonias, escribir_salidas, validar_anuncios
from arraigo.pipeline.colonias import RAIZ, cargar_catalogo
from arraigo.pipeline.reporte import construir_reporte, escribir_reporte

raw, out = RAIZ / "data" / "raw", RAIZ / "data" / "processed"
catalogo = cargar_catalogo()
validos, rechazados = validar_anuncios(raw, catalogo)
escribir_salidas(out, validos, rechazados, construir_colonias(catalogo, validos))
reporte = construir_reporte(validos, rechazados)
escribir_reporte(out, reporte)
print(f"válidos={reporte['validos']} rechazados={reporte['rechazados']} fraudes={reporte['fraudes_prueba']} -> {out}")
