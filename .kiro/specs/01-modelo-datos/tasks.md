# Tareas — Spec 01: Modelo de datos y dataset base

- [x] 1. Esquemas Pydantic
  - [x] 1.1 Crear `src/arraigo/schemas/inmueble.py` con `Operacion`, `Requisito`, `Inmueble` y el validador de ubicación aproximada (contexto `centroides`)
    - _Requerimientos: R1.1, R1.2, R1.3_
  - [x] 1.2 Crear `src/arraigo/schemas/perfil.py` con `Ubicacion` y `Perfil`, incluyendo rangos y validador de enganche/prioridades
    - _Requerimientos: R2.1, R2.2_
  - [x] 1.3 Crear `src/arraigo/schemas/colonia.py` con `Dato[T]`, `Punto`, `Estacion`, `NivelRiesgo`, `PuntoComunidad`, `Colonia`
    - _Requerimientos: R3.1, R3.2_
  - [x] 1.4 Exportar todo en `src/arraigo/schemas/__init__.py`
  - [x] 1.5 Pruebas unitarias `tests/test_schema_inmueble.py`, `test_schema_perfil.py`, `test_schema_colonia.py` (casos en design.md)
    - _Requerimientos: R5.1_

- [ ] 2. Datos de colonias
  - [x] 2.1 ~~(Humano) Descargar el catálogo de colonias CDMX en GeoJSON~~ → reemplazado por centroides manuales (columnas lat/lng en `colonias_piloto.csv`) a `data/raw/colonias_cdmx.geojson` y anotar URL + fecha en `data/raw/FUENTES.md`
  - [x] 2.2 Crear `src/arraigo/pipeline/colonias.py`: normalizar nombres, cruzar `colonias_piloto.csv` con el GeoJSON y calcular centroides
    - _Requerimientos: R3.1, R3.3_
  - [x] 2.3 Prueba: las 13 colonias piloto hacen match con el catálogo

- [ ] 3. Anuncios
  - [ ] 3.1 (Humano) Capturar 3 anuncios reales por colonia en `data/raw/anuncios_reales.csv` (columnas = campos de `Inmueble`, `fuente=captura_manual:<portal>`, con `url_origen`)
    - _Requerimientos: R4.1_
  - [x] 3.2 Crear `scripts/generar_anuncios_sinteticos.py` según design.md (semilla fija, ~300 registros, ≥ 20 fraudes)
    - _Requerimientos: R4.2, R4.3_
  - [x] 3.3 Crear `src/arraigo/pipeline/cargar.py`: leer todos los `data/raw/anuncios_*.csv`, validar, escribir `inmuebles.json` y `rechazados.jsonl`
    - _Requerimientos: R1.3, R4.1_
  - [x] 3.4 Calcular medianas de precio m2 por colonia y operación (solo anuncios reales) y escribir `colonias.json`
    - _Requerimientos: R3.1, R3.3_
  - [x] 3.5 Crear `src/arraigo/pipeline/reporte.py`: reporte de calidad en JSON y Markdown
    - _Requerimientos: R4.4_
  - [x] 3.6 Crear `scripts/cargar_dataset.py` que corra 2.2 → 3.3 → 3.4 → 3.5

- [ ] 4. Verificación
  - [x] 4.1 `tests/test_cargar_dataset.py` con los criterios de design.md
    - _Requerimientos: R5.2_
  - [ ] 4.2 `uv run pytest` en verde y `reporte_calidad.md` revisado por el equipo
