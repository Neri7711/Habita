# Orquestación: trabajo en paralelo con Kiro

> **Ronda 1 (A-F) TERMINADA** — en `main` quedó la versión de GB3tou (commit `81c4e51`) + specs 02 y 04.
> La versión local de Kiro de A-C quedó respaldada en la rama local `respaldo/kiro-carriles-abc` (no se usa).
> ⚠️ Para no duplicar trabajo otra vez: **cada carril tiene UN dueño** (columna "Quién"). Si no es tuyo, no lo corras.

## Ronda 2

| Carril | Quién | Qué hace | Archivos que le pertenecen |
|---|---|---|---|
| G | Kiro en laptop de Neri | Implementar spec 02 (enriquecimiento de colonias) | `src/arraigo/pipeline/enriquecer/`, `scripts/enriquecer_colonias.py`, `tests/enriquecer/`, `src/arraigo/schemas/colonia.py` (solo si la spec lo pide), `data/raw/` (descargas nuevas), `data/raw/FUENTES.md` |
| H | Kiro en laptop de Neri | Implementar spec 04 (antifraude) | `src/arraigo/antifraude/`, `scripts/evaluar_antifraude.py`, `data/raw/antifraude_reglas.json`, `tests/test_antifraude_*.py` |
| I | Kiro en laptop de Neri | Escribir spec 03 (costo real + precio justo), solo documentos | `.kiro/specs/03-costo-real-precio-justo/*` |
| J | Kiro en laptop de Neri | Escribir spec 05 (agente MCP), solo documentos | `.kiro/specs/05-agente-mcp/*` |

### Prompt carril G
```
Lee #steering, data/raw/FUENTES.md y .kiro/specs/02-enriquecimiento-colonias (requirements, design, tasks).
Ejecuta las tareas de esa spec en orden. Usa los clientes de src/arraigo/fuentes/ (ya probados; tokens en INEGI_TOKEN y BANXICO_TOKEN).
Solo puedes crear/editar: src/arraigo/pipeline/enriquecer/, scripts/enriquecer_colonias.py, tests/enriquecer/,
data/raw/ (archivos nuevos descargados) y data/raw/FUENTES.md; src/arraigo/schemas/colonia.py solo si una tarea lo exige.
No toques src/arraigo/antifraude/ ni .kiro/specs/03 o 05 (otros carriles). No hagas commit.
Termina con uv run python scripts/enriquecer_colonias.py y uv run pytest, y marca las tareas en tasks.md.
```

### Prompt carril H
```
Lee #steering y .kiro/specs/04-antifraude (requirements, design, tasks).
Ejecuta las tareas de esa spec en orden, usando data/processed/inmuebles.json (genéralo con uv run python scripts/cargar_dataset.py si no existe).
Solo puedes crear/editar: src/arraigo/antifraude/, scripts/evaluar_antifraude.py, data/raw/antifraude_reglas.json, tests/test_antifraude_*.py.
No toques schemas, pipeline ni otras specs. No hagas commit.
Termina con uv run python scripts/evaluar_antifraude.py (muestra precisión y recall contra es_fraude_prueba) y uv run pytest; marca tasks.md.
```

### Prompt carril I
```
Usa el modo Spec. Lee #steering, .kiro/specs/01-modelo-datos y src/arraigo/schemas/ para usar los modelos reales.
Crea .kiro/specs/03-costo-real-precio-justo/ (requirements.md, design.md, tasks.md, formato EARS en español) para:
traslado estimado (haversine × factor de rodeo ÷ velocidad por modo; destino geocodificado con arraigo.fuentes.nominatim),
costo de transporte con tarifas oficiales SEMOVI en tabla fija, tiempo valorizado (ingreso/hora × horas de traslado al mes),
servicios (supuesto documentado), mensualidad de compra (amortización con tasa de referencia de Banxico vía arraigo.fuentes.banxico + enganche),
y precio justo (precio/m2 vs mediana de la colonia, con banda "justo / caro / sospechosamente barato").
Todo determinista, con fuente y supuestos explícitos. Código en src/arraigo/calculos/. Solo documentos, no escribas código.
```

### Prompt carril J
```
Usa el modo Spec. Lee #steering (sobre todo tech.md: Kiro es el LLM vía MCP) y las specs 01-04.
Crea .kiro/specs/05-agente-mcp/ (requirements.md, design.md, tasks.md, formato EARS en español) para un servidor MCP en Python (paquete mcp, FastMCP)
en src/arraigo/mcp_server.py con herramientas: buscar_inmuebles(perfil) con ranking por prioridades, costo_real, precio_justo, score_fraude, info_colonia,
y alternativas_equilibradas (reubicación consciente). Cada respuesta incluye explicación, fuentes y avisos (sintético, ubicación aproximada).
Incluye el registro en .kiro/settings/mcp.json y un guion de demo con 3 perfiles. No incluye front. Solo documentos, no escribas código.
```

---

## Ronda 1 (histórico)

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
- **H1**: ~~descargar a mano el catálogo de colonias~~ → ahora lo hace el carril B con `arraigo.fuentes.datos_cdmx` (dataset `colonias-del-iecm-2022`). Humano solo: sacar tokens gratuitos de INEGI DENUE y Banxico SIE para la spec 02/03.
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
Para obtener data/raw/colonias_cdmx.geojson usa arraigo.fuentes.datos_cdmx.buscar_datasets("colonias-del-iecm-2022")
y arraigo.fuentes._http.descargar sobre el recurso GeoJSON (si solo hay SHP/ZIP, avísame). Anota fecha en data/raw/FUENTES.md.
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
Cada dato con fuente y fecha_dato. Nada de scraping. Diseña sobre los clientes ya existentes en src/arraigo/fuentes/
(lee data/raw/FUENTES.md). Solo documentos, no escribas código.
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
