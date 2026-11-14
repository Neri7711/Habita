# Tareas — Spec 05: Agente MCP

Convenciones: ejecutar todo con `uv run`. Cada tarea indica los requisitos que cumple. No tocar el front.
Prerrequisitos: specs 01 y 04 implementadas, spec 03 implementada (`arraigo.calculos`), y `data/processed/inmuebles.json` y `colonias.json` generados.
La spec 02 mejora los datos de colonia, pero el servidor funciona con campos vacíos (avisa "sin dato").

- [ ] 1. Preparación
  - [ ] 1.1 `uv add mcp` (solo esta dependencia nueva) y comprobar `from mcp.server.fastmcp import FastMCP`. _R1.1_
  - [ ] 1.2 Crear `src/arraigo/agente/` con `__init__.py`. _Estructura_
  - [ ] 1.3 Confirmar los nombres reales de las funciones de las specs 03 y 04 y ajustar la tabla "Dependencias entre specs" de `design.md` si difieren. _Contrato_

- [ ] 2. Núcleo del agente (sin MCP)
  - [ ] 2.1 `envoltorio.py`: `Fuente`, `Envoltorio`, constantes de avisos, helper para deduplicar avisos y para devolver errores en español. _R2.1-2.4, R2.8_
  - [ ] 2.2 `contexto.py`: `ContextoAgente` y `cargar_contexto()`; construir `ContextoAntifraude`, precalcular scores, error claro si faltan archivos. _R1.4, R1.5_
  - [ ] 2.3 `ranking.py`: filtros duros, criterios 0-1, pesos por posición reescalados, `puntuar()`, desempate por id. _R3.2-3.8, R3.11_
  - [ ] 2.4 `explicaciones.py`: plantillas de `por_que`, resumen de costo, sugerencia de integración, texto de presión de gentrificación. Cada cifra viene de un parámetro, ninguna escrita a mano. _R3.9, R7.5, R7.6, R8.5_
  - [ ] 2.5 Pruebas: `tests/test_agente_ranking.py` (pesos, normalización, dato faltante, determinismo). _R3, R10.3_

- [ ] 3. Herramientas como funciones puras (`herramientas.py`)
  - [ ] 3.1 `info_colonia`: normalización de nombre, coincidencia única, lista de piloto si es ambigua, procedencia por campo, sugerencia de integración. _R7_
  - [ ] 3.2 `precio_justo` y `score_fraude`: adaptadores a spec 03 y spec 04; ocultar `es_fraude_prueba`; remitir a `score_fraude` en banda barata; aviso de "no garantiza". _R5, R6_
  - [ ] 3.3 `costo_real`: adaptador a spec 03; supuestos con valor en la explicación; aviso hipotecario en venta; ids parecidos si no existe. _R4_
  - [ ] 3.4 `buscar_inmuebles`: filtros, exclusión de riesgo alto con conteo, ranking, `por_que`, lista vacía con filtro a relajar, avisos de sintético y ubicación aproximada. _R3, R2.2-2.3_
  - [ ] 3.5 `alternativas_equilibradas`: umbral de presión, ranking restringido, mejor anuncio por colonia, comparación con origen, máx. 3, sin relleno. _R8_
  - [ ] 3.6 Pruebas: `tests/test_agente_herramientas.py` con contexto pequeño a mano y sin red; incluir la prueba de que ninguna salida contiene "estafa" ni `es_fraude_prueba`. _R2.7, R6.2, R10.3_

- [ ] 4. Servidor MCP
  - [ ] 4.1 `mcp_server.py`: instancia `FastMCP("arraigo", instructions=...)`, registrar las seis herramientas con docstrings en español y `readOnlyHint=True`, `main()` con transporte `stdio`, logging a `stderr`, bloque `if __name__ == "__main__"`. _R1.1, R1.6, R9.1, R9.3_
  - [ ] 4.2 Manejo de errores: capturar `ValidationError` y `ErrorDatos` y devolver `Envoltorio(ok=False)`; ninguna excepción sin controlar sale al cliente. _R2.8, R1.4_
  - [ ] 4.3 Fallos de red: usar caché o valor de respaldo de la spec 03 y agregar aviso. _R10.2_
  - [ ] 4.4 Pruebas: `tests/test_mcp_server.py` con cliente MCP en memoria: lista 6 herramientas, llama a cada una, comprueba anotaciones e `instructions`. _R10.4_

- [ ] 5. Registro y guía para Kiro
  - [ ] 5.1 Leer `.kiro/settings/mcp.json` (workspace) y `~/.kiro/settings/mcp.json`; crear o fusionar la entrada `arraigo` sin borrar otros servidores y sin tokens. _R1.2, R1.3_
  - [ ] 5.2 Crear `.kiro/steering/agente.md` con las reglas de `instructions` y la lista de cosas que Kiro debe rechazar (contactar caseros, pagos, contratos, asesoría vinculante). _R9.2, R9.4_
  - [ ] 5.3 Verificación manual: `uv run python -m arraigo.mcp_server` arranca; Kiro lista las seis herramientas en el panel MCP. _R1.1_

- [ ] 6. Demo
  - [ ] 6.1 `data/raw/demo_perfiles.json` con los 3 perfiles de `design.md` y `tests/test_demo_perfiles.py` que los valida con `Perfil`. _R11.2, R11.3_
  - [ ] 6.2 `scripts/capturar_demo.py` (solo llama a `herramientas.py` y escribe el texto) para generar las respuestas del plan B. _R11.4_
  - [ ] 6.3 `docs/demo_agente.md`: preparación, 3 perfiles con mensaje, herramientas esperadas, qué debe verse, avisos que se dicen en voz alta, plan B con respuestas capturadas. _R11.1, R11.4_
  - [ ] 6.4 Ensayo completo en el chat de Kiro con los 3 mensajes; ajustar docstrings de herramientas si Kiro elige mal la herramienta. _R11_

- [ ] 7. Cierre
  - [ ] 7.1 `uv run pytest` completo en verde, sin red ni tokens. _R10.3_
  - [ ] 7.2 Medir tiempo de cada herramienta con el dataset completo (< 2 s). _R10.1_
  - [ ] 7.3 Revisar que ninguna respuesta incluya `es_fraude_prueba`, "estafa" ni coordenadas exactas presentadas como reales cuando `ubicacion_aproximada` es verdadero. _R2.3, R2.7, R6.2_
  - [ ] 7.4 Marcar las tareas completadas; no hacer commit.

## Orden y dependencias
```
1 ─► 2 ─► 3.1 ─► 3.2 ─► 3.3 ─► 3.4 ─► 3.5 ─► 3.6 ─► 4 ─► 5 ─► 6 ─► 7
```
3.2 y 3.3 requieren las specs 04 y 03; 3.4 y 3.5 requieren 3.1-3.3. La tarea 6.1 puede adelantarse en paralelo desde el inicio.
