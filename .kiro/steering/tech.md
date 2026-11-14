# Stack técnico

Prioridad #1: **velocidad de hackatón**. Nada de infraestructura que no se pueda correr en una laptop sin cuentas extra.

## Base
- Python 3.12+ gestionado con **uv** (`uv sync`, `uv run ...`). No usar pip directo.
- **Pydantic v2** para todos los esquemas y validación.
- **pandas** para carga/transformación del dataset.
- **pytest** para pruebas.
- Datos en archivos: `data/raw/` (entrada, versionada) → `data/processed/` (salida generada, JSON/Parquet).
  Si hace falta consultar, usar DuckDB sobre esos archivos. Sin servidor de base de datos.

## LLM
- No tenemos API key de ningún LLM: los créditos son de **Kiro**.
- Por eso el agente se implementa como **servidor MCP en Python** (paquete `mcp`, FastMCP) que expone herramientas
  deterministas (`buscar_inmuebles`, `costo_real`, `precio_justo`, `score_fraude`, `info_colonia`).
- Kiro se conecta al servidor vía `.kiro/settings/mcp.json` y **el chat de Kiro es la interfaz del agente** en la demo.
- El código del proyecto nunca llama a un LLM directamente.

## Servicios externos (solo gratuitos, sin API key de pago)
- Geocodificación: Nominatim (OSM), máx. 1 req/s, con caché en disco.
- Traslado: estimación determinista (distancia haversine × factor de rodeo ÷ velocidad por modo). Documentar supuestos.
- Datos oficiales: descargar archivos a mano a `data/raw/` y registrar URL + fecha en `data/raw/FUENTES.md`.

## Convenciones
- Código, nombres de campos y mensajes en **español sin acentos** en identificadores (`banos`, `alcaldia`), con acentos en textos.
- Montos en MXN como `int` (sin centavos). Coordenadas en WGS84 (`lat`, `lng` float).
- Funciones puras para cálculos; I/O solo en `arraigo/pipeline/` y `scripts/`.
- Cada valor derivado de una fuente lleva `fuente` y `fecha_dato`.
- Windows: rutas con `pathlib`, archivos en UTF-8 explícito.
