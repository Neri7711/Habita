# Estructura del repo

```
Habita/
├── .kiro/
│   ├── steering/            # contexto permanente (producto, stack, estructura)
│   └── specs/NN-nombre/     # requirements.md, design.md, tasks.md por fase
├── data/
│   ├── raw/                 # entradas versionadas (CSV/JSON/GeoJSON) + FUENTES.md
│   └── processed/           # salidas generadas por el pipeline (no editar a mano)
├── src/arraigo/
│   ├── schemas/             # modelos Pydantic: inmueble, perfil, colonia
│   ├── pipeline/            # carga, validación, reporte de calidad
│   ├── calculos/            # (spec 03) costo real, precio justo
│   ├── antifraude/          # (spec 04) reglas y score
│   └── mcp_server.py        # (spec 05) herramientas expuestas a Kiro
├── scripts/                 # CLIs puntuales (generar sintéticos, cargar dataset)
└── tests/                   # pytest, espejo de src/arraigo/
```

Reglas:
- Un módulo por esquema. Nada de lógica de negocio en `scripts/`; los scripts solo llaman funciones de `arraigo`.
- Toda función pública nueva lleva prueba en `tests/`.
- Ejecutar todo con `uv run`: `uv run pytest`, `uv run python scripts/cargar_dataset.py`.
