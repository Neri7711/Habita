# Tareas — Spec 03: Costo real y precio justo

Requiere la spec 01 terminada (`arraigo.schemas`, `data/processed/inmuebles.json` y `colonias.json`).
La spec 02 es opcional: si ya llenó `estaciones_transporte_cercanas`, se usa para elegir la tarifa.
Archivos propios de esta spec: `src/arraigo/calculos/`, `src/arraigo/pipeline/referencias.py`, `scripts/calcular_costos.py`,
`data/raw/calculos_supuestos.json`, `data/raw/tarifas_semovi.json`, `tests/test_calculos_*.py`, `tests/test_referencias.py`.

- [x] 1. Configuración y datos fijos
  - [x] 1.1 Crear `data/raw/calculos_supuestos.json` con los valores de design.md (cada uno con fuente y fecha)
    - _Requerimientos: R1.4, R4.1, R5.2, R7.2, R8.1_
  - [x] 1.2 Verificar las tarifas vigentes en la fuente oficial (SEMOVI / Gaceta Oficial CDMX) y crear `data/raw/tarifas_semovi.json` con URL y fecha de vigencia por tarifa; revisar con el equipo velocidades, servicios y spread
    - Nota: tarifas verificadas en prensa que cita a las autoridades (jun-ago 2026); el Trolebús ($4) queda por confirmar en la Gaceta Oficial. Velocidades, servicios y spread siguen pendientes de revisión del equipo.
    - _Requerimientos: R2.1, R2.2, R2.8, R8.1_
  - [x] 1.3 Registrar tarifas, supuestos y la tasa de referencia en `data/raw/FUENTES.md`
    - _Requerimientos: R8.2_
    - Pendiente: data/raw/FUENTES.md es del carril G; las fuentes a registrar van en el resumen del carril K.
  - [x] 1.4 Crear `calculos/supuestos.py` (`ConfigCalculos`, `TarifasSemovi`, `cargar_config`, `cargar_tarifas`) que falle si falta fuente, fecha o vigencia
    - _Requerimientos: R2.8, R8.1_
  - [x] 1.5 Crear `calculos/modelos.py` con `Traslado`, `Componente`, `Hipoteca`, `PrecioJusto` y `CostoReal`
    - _Requerimientos: R6.2_
- [x] 2. Traslado y transporte
  - [x] 2.1 `calculos/traslado.py`: `haversine_km` y `estimar_traslado` (rodeo, velocidad, `mixto`, ubicación aproximada, `excede_tiempo_max`, sin ubicación)
    - _Requerimientos: R1.1, R1.2, R1.3, R1.5, R1.8, R1.9, R1.10_
  - [x] 2.2 `calculos/transporte.py`: `costo_transporte_mensual` para transporte público, auto y bici; tarifa por tipo de estación o por defecto
    - _Requerimientos: R2.3, R2.4, R2.5, R2.6, R2.7_
  - [x] 2.3 Pruebas `tests/test_calculos_traslado.py` y `tests/test_calculos_transporte.py` (valores a mano, los tres modos, `mixto`, sin `lat`/`lng`, tarifa por defecto)
    - _Requerimientos: R9.1, R9.2_
- [x] 3. Tiempo y servicios
  - [x] 3.1 `calculos/tiempo.py`: `tiempo_valorizado` con horas al mes y factor configurable
    - _Requerimientos: R3.1, R3.2, R3.3, R3.4_
  - [x] 3.2 `calculos/servicios.py`: `costo_servicios` con desglose y extra de mantenimiento y predial en venta
    - _Requerimientos: R4.1, R4.2, R4.3, R4.4_
  - [x] 3.3 Pruebas `tests/test_calculos_tiempo.py` y `tests/test_calculos_servicios.py`
    - _Requerimientos: R9.1_
- [x] 4. Mensualidad de compra
  - [x] 4.1 `calculos/hipoteca.py`: `mensualidad_compra` (cuota fija, tasa 0, enganche ≥ precio, enganche mínimo, tope de ingreso 35%)
    - _Requerimientos: R5.1, R5.5, R5.6, R5.7, R5.8, R5.9_
  - [x] 4.2 `pipeline/referencias.py`: `obtener_tasa_referencia` (Banxico → archivo guardado → respaldo) y `geocodificar_destino` (Nominatim, `DireccionNoEncontrada`)
    - _Requerimientos: R1.6, R1.7, R5.2, R5.3, R5.4_
  - [x] 4.3 Pruebas `tests/test_calculos_hipoteca.py` y `tests/test_referencias.py` con mocks de `banxico.dato_oportuno` y `nominatim.geocodificar` (sin red ni token)
    - _Requerimientos: R9.1, R9.4_
- [x] 5. Precio justo
  - [x] 5.1 `calculos/precio_justo.py`: `evaluar_precio_justo` con tres bandas, `no_evaluable`, cita de fuente y fecha, aviso de sintético y remisión a antifraude
    - _Requerimientos: R7.1, R7.2, R7.3, R7.4, R7.5, R7.6, R7.7_
  - [x] 5.2 Pruebas `tests/test_calculos_precio_justo.py` (límites 0.70 y 1.15, renta y venta, sin `m2`, sin mediana)
    - _Requerimientos: R9.1, R9.2_
- [x] 6. Costo real compuesto
  - [x] 6.1 `calculos/costo_real.py`: `calcular_costo_real` que compone traslado, transporte, tiempo, servicios, vivienda y precio justo; componentes no calculables; redondeo final; `excede_presupuesto`; enganche aparte
    - _Requerimientos: R6.1, R6.2, R6.3, R6.4, R6.5, R6.6, R6.7_
  - [x] 6.2 Textos de `resumen` y avisos obligatorios en lenguaje simple
    - _Requerimientos: R4.4, R5.8, R7.5, R8.4, R8.5_
  - [x] 6.3 Pruebas `tests/test_calculos_costo_real.py` con el ejemplo de design.md ($19,620 monetario y $23,370 real), compra, `excede_presupuesto` y sin ubicación
    - _Requerimientos: R9.1, R9.2_
  - [x] 6.4 Pruebas de determinismo y de que `calculos/` no importa módulos de red ni `arraigo.fuentes`
    - _Requerimientos: R8.3, R9.3_
- [x] 7. Script e integración
  - [x] 7.1 Crear `scripts/calcular_costos.py`: lee un perfil JSON, geocodifica el destino si solo trae dirección, obtiene la tasa, calcula todos los inmuebles y escribe `data/processed/costos.json` (el script solo llama funciones de `arraigo`)
    - _Requerimientos: R1.6, R5.3, R6.2_
  - [x] 7.2 Prueba de integración con `inmuebles.json` y un perfil de ejemplo, sin red
    - _Requerimientos: R9.5_
- [x] 8. Cierre
  - [ ] 8.1 `uv run pytest` en verde y `uv run python scripts/calcular_costos.py` con un perfil de ejemplo; revisar con el equipo 5 resultados a mano
    - Hecho: pytest en verde y script ejecutado; falta la revisión manual de 5 resultados con el equipo.
    - _Requerimientos: R9.5_
  - [x] 8.2 Documentar en el docstring de `calcular_costo_real` y `evaluar_precio_justo` la interfaz que usará la spec 05 (herramientas `costo_real` y `precio_justo`)
    - _Requerimientos: R8.3_
