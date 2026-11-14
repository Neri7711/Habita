# Orquestación: trabajo en paralelo con Kiro

Cada carril = **un chat/agente de Kiro distinto**, todos sobre este mismo repo.
Regla de oro: **cada carril solo toca SUS archivos**. Nadie toca el front. Nadie hace commit ni push (eso lo hace Neri).

| Carril | Qué hace | Archivos que le pertenecen | Depende de |
|---|---|---|---|
| A | Esquemas Inmueble + Perfil + pruebas | `src/arraigo/schemas/inmueble.py`, `perfil.py`, `__init__.py`, `tests/test_schema_inmueble.py`, `tests/test_schema_perfil.py` | — |
| B | Esquema Colonia + centroides | `src/arraigo/schemas/colonia.py`, `src/arraigo/pipeline/colonias.py`, `tests/test_schema_colonia.py`, `tests/test_colonias.py`, `pyproject.toml` (solo `uv add shapely`) | GeoJSON (humano) para probar centroides |
| C | Generador de anuncios sintéticos | `scripts/generar_anuncios_sinteticos.py`, `tests/test_generador.py` | — (lee columnas de design.md) |
| D | Spec 02 en modo Spec de Kiro (solo documentos) | `.kiro/specs/02-enriquecimiento-colonias/*` | — |
| E | Spec 04 en modo Spec de Kiro (solo documentos) | `.kiro/specs/04-antifraude/*` | — |
| F | Carga + reporte de calidad | `src/arraigo/pipeline/cargar.py`, `reporte.py`, `scripts/cargar_dataset.py`, `tests/test_cargar_dataset.py` | **A, B y C terminados** (segunda ronda) |

Humanos en paralelo (no Kiro):
- **H1**: descargar el catálogo de colonias de Datos Abiertos CDMX → `data/raw/colonias_cdmx.geojson` y llenar `data/raw/FUENTES.md`.
- **H2**: capturar a mano 3-5 anuncios reales por colonia (renta y venta) → `data/raw/anuncios_reales.csv`.

---

## Prompt carril A
```
Lee #steering y #.kiro/specs/01-modelo-datos (requirements.md, design.md, tasks.md).
Ejecuta las tareas 1.1, 1.2, 1.4 y la parte de 1.5 de inmueble y perfil.
Solo puedes crear/editar: src/arraigo/schemas/inmueble.py, perfil.py, __init__.py,
tests/test_schema_inmueble.py, tests/test_schema_perfil.py.
En __init__.py exporta también lo de colonia.py con import tolerante si aún no existe.
No toques ningún otro archivo, no hagas commit. Termina corriendo: uv run pytest tests/test_schema_inmueble.py tests/test_schema_perfil.py
y marca las tareas en tasks.md.
```

## Prompt carril B
```
Lee #steering y #.kiro/specs/01-modelo-datos.
Ejecuta las tareas 1.3 (colonia.py + su prueba) y 2.2-2.3 (pipeline/colonias.py).
Solo puedes crear/editar: src/arraigo/schemas/colonia.py, src/arraigo/pipeline/colonias.py,
tests/test_schema_colonia.py, tests/test_colonias.py. Para dependencias usa solo `uv add shapely`.
NO edites src/arraigo/schemas/__init__.py (es del carril A).
Si data/raw/colonias_cdmx.geojson no existe todavía, haz que la prueba de match se marque como skip con mensaje claro.
No hagas commit. Termina con uv run pytest tests/test_schema_colonia.py tests/test_colonias.py y marca las tareas.
```

## Prompt carril C
```
Lee #steering y la sección "Generador sintético" de #.kiro/specs/01-modelo-datos/design.md.
Ejecuta la tarea 3.2. Solo puedes crear: scripts/generar_anuncios_sinteticos.py y tests/test_generador.py.
Escribe a data/raw/anuncios_sinteticos.csv con exactamente las columnas del modelo Inmueble de design.md.
Calibra con data/raw/anuncios_reales.csv si existe; si no, usa una tabla de medianas PROVISIONAL dentro del script,
marcada con un comentario "PROVISIONAL - reemplazar con medianas reales" y fuente="sintetico".
No importes de arraigo.schemas (otro carril lo está escribiendo). Semilla fija. No hagas commit.
Termina corriendo el script y uv run pytest tests/test_generador.py.
```

## Prompt carril D
```
Usa el modo Spec. Lee #steering y #.kiro/specs/01-modelo-datos para mantener el mismo formato (EARS, español).
Crea .kiro/specs/02-enriquecimiento-colonias/ con requirements.md, design.md y tasks.md para llenar en el esquema Colonia:
indice_delitos (carpetas de investigación FGJ, Datos Abiertos CDMX), estaciones_transporte_cercanas (GTFS SEMOVI y Ecobici),
nivel_riesgo (Atlas de Riesgos CDMX), puntos_comunidad (OpenStreetMap/Overpass y DENUE INEGI)
e indicador_presion_gentrificacion (densidad Inside Airbnb + cambio Censo INEGI 2010-2020 por AGEB, fórmula documentada).
Cada dato con fuente y fecha_dato. Descargas manuales a data/raw/, nada de scraping. Solo documentos, no escribas código.
```

## Prompt carril E
```
Usa el modo Spec. Lee #steering y #.kiro/specs/01-modelo-datos para mantener el formato.
Crea .kiro/specs/04-antifraude/ con requirements.md, design.md y tasks.md: reglas deterministas (precio < 50% de la mediana,
pide depósito antes de visitar, sin dirección, contacto solo por WhatsApp, descripción duplicada, etc.),
un score 0-100 explicable en lenguaje simple por cada señal, y una evaluación contra es_fraude_prueba
(precisión y recall). Solo documentos, no escribas código.
```

## Prompt carril F (segunda ronda, cuando A, B y C estén en verde)
```
Lee #steering y #.kiro/specs/01-modelo-datos. Ejecuta las tareas 3.3, 3.4, 3.5, 3.6 y 4.1.
Solo puedes crear: src/arraigo/pipeline/cargar.py, reporte.py, scripts/cargar_dataset.py, tests/test_cargar_dataset.py.
Usa los esquemas de arraigo.schemas y pipeline/colonias.py tal como están; si algo no te cuadra, avísame en vez de editarlos.
No hagas commit. Termina con uv run python scripts/cargar_dataset.py, uv run pytest y muéstrame reporte_calidad.md.
```
