"""Prueba rápida de que las fuentes gratuitas responden. Uso: uv run python scripts/probar_fuentes.py"""

from arraigo.fuentes import datos_cdmx, nominatim, overpass

print("Datos Abiertos CDMX:")
for d in datos_cdmx.buscar_datasets("colonias", 3):
    print("  -", d["name"], "|", d["title"])
print("Nominatim:", nominatim.geocodificar("Paseo de la Reforma 222, Ciudad de México"))
pts = overpass.puntos_cercanos(19.4194, -99.1617)  # Roma Norte aprox.
print(f"Overpass: {len(pts)} puntos cerca de Roma Norte, ej.", pts[:2])
