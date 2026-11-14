# Requisitos — Spec 05: Agente MCP

## Introducción
Servidor MCP en Python (paquete `mcp`, FastMCP) que expone como herramientas los cálculos deterministas de las specs 01-04.
Kiro es el LLM: conversa, elige herramientas y redacta; el servidor filtra, calcula, ordena y entrega datos con explicación, fuentes y avisos.
El código del proyecto nunca llama a un LLM. No hay front en esta spec: la interfaz de la demo es el chat de Kiro.

Depende de: spec 01 (esquemas y `data/processed/inmuebles.json`, `colonias.json`), spec 02 (campos enriquecidos de colonia),
spec 03 (`arraigo.calculos`: costo real y precio justo) y spec 04 (`arraigo.antifraude`: score).

## Glosario
- **Servidor**: `src/arraigo/mcp_server.py`.
- **Herramienta**: función expuesta por el Servidor a Kiro.
- **Envoltorio**: estructura común de toda respuesta (`datos`, `explicacion`, `fuentes`, `avisos`).
- **Perfil**: modelo `Perfil` de `arraigo.schemas`.
- **Aviso**: texto fijo que el agente debe mostrar al usuario (sintético, ubicación aproximada, datos faltantes).

## Requisitos

### R1. Arranque y registro
**Historia:** Como integrante del equipo, quiero que Kiro se conecte al servidor con un solo registro, para demostrar el agente sin infraestructura extra.
1. CUANDO se ejecute `uv run python -m arraigo.mcp_server`, EL Servidor DEBE iniciar con transporte `stdio` y registrar las seis herramientas de R3-R8.
2. EL repositorio DEBE incluir el registro del Servidor en `.kiro/settings/mcp.json` (comando `uv`, argumentos `run python -m arraigo.mcp_server`, `cwd` en la raíz del proyecto).
3. EL registro NO DEBE contener tokens ni secretos; `INEGI_TOKEN` y `BANXICO_TOKEN` se leen del entorno del sistema.
4. CUANDO falte `data/processed/inmuebles.json` o `colonias.json`, EL Servidor DEBE iniciar de todos modos y cada herramienta DEBE responder con un error claro que indique el comando para generarlos (`uv run python scripts/cargar_dataset.py`).
5. EL Servidor DEBE cargar los datos una sola vez al iniciar (en memoria) y NO DEBE escribir en `data/` ni en ningún otro archivo, salvo la caché de geocodificación de la spec 03.
6. EL Servidor NO DEBE escribir en `stdout` nada que no sea protocolo MCP; los registros (logs) van a `stderr`.

### R2. Envoltorio común de respuesta
**Historia:** Como usuario, quiero saber por qué se me recomienda algo y de dónde sale cada dato, para poder confiar en el agente.
1. TODA herramienta DEBE devolver un Envoltorio con: `datos` (resultado estructurado), `explicacion` (texto en español sencillo, sin jerga inmobiliaria), `fuentes` (lista de `{descripcion, fecha_dato}`) y `avisos` (lista de textos).
2. CUANDO un resultado incluya un inmueble con `fuente = "sintetico"`, EL Servidor DEBE agregar el aviso: "Este anuncio es de ejemplo (sintético), no es una oferta real."
3. CUANDO un inmueble tenga `ubicacion_aproximada = true`, EL Servidor DEBE agregar el aviso: "La ubicación es aproximada (centro de la colonia), no la dirección del inmueble."
4. CUANDO un dato requerido no exista (mediana de colonia, estaciones, índice de delitos), EL Servidor DEBE devolverlo como `null`, listarlo en `avisos` ("No hay dato de X para Y") y NO DEBE inventar ni rellenar un valor.
5. EL Servidor DEBE incluir en `fuentes` la `fuente` y `fecha_dato` de cada `Dato` de colonia que haya usado en el cálculo.
6. TODOS los montos DEBEN ir en MXN como entero y las coordenadas en WGS84 (`lat`, `lng`).
7. EL Servidor NO DEBE usar las palabras "estafa" ni "fraude confirmado"; DEBE hablar de "señales de riesgo".
8. CUANDO una herramienta reciba entrada inválida, EL Servidor DEBE devolver un error con el campo y el motivo en español (por ejemplo, "prioridades: no puede tener repetidos") y NO DEBE lanzar una excepción sin controlar.

### R3. Herramienta `buscar_inmuebles(perfil)`
**Historia:** Como persona que se reubica, quiero opciones ordenadas según lo que me importa, para decidir rápido.
1. LA herramienta DEBE recibir un `Perfil` completo (validado con el esquema de la spec 01) y un `limite` opcional (por defecto 5, máximo 10).
2. LA herramienta DEBE filtrar de forma excluyente por: operación (`renta` → `renta`; `compra` → `venta`; `ambas` → las dos), `precio <= presupuesto_max_mxn`, `recamaras >= recamaras_min`, y `acepta_mascotas` distinto de `false` cuando `mascotas = true`.
3. CUANDO el Perfil tenga `tiene_aval = false`, LA herramienta DEBE excluir los anuncios de renta cuyos `requisitos` incluyan `aval`.
4. LA herramienta DEBE excluir los anuncios cuyo traslado estimado supere `tiempo_max_traslado_min` (estimación de la spec 03).
5. LA herramienta DEBE excluir los anuncios con `score_riesgo` de nivel `alto` de la spec 04, y DEBE reportar cuántos excluyó por esta razón en `datos.excluidos_por_riesgo`.
6. LA herramienta DEBE ordenar con una puntuación 0-100 por anuncio, combinando criterios normalizados (0-1) con pesos derivados de `prioridades` en orden descendente: pesos {5 prioridades: 0.35, 0.25, 0.20, 0.12, 0.08} reescalados a la cantidad recibida (la primera prioridad pesa más).
7. LOS criterios DEBEN ser: `precio` (menor costo real mensual es mejor), `traslado` (menor tiempo es mejor), `seguridad` (menor `indice_delitos` de la colonia es mejor), `comunidad` (más `puntos_comunidad` y estaciones cercanas es mejor), `espacio` (más m² es mejor).
8. CUANDO el dato de un criterio falte para una colonia, LA herramienta DEBE asignarle el valor neutro 0.5 en ese criterio y DEBE avisarlo en el resultado de ese anuncio.
9. CADA resultado DEBE incluir: el `Inmueble`, `puntuacion`, `desglose` (aporte por prioridad), `costo_real` resumido, `precio_justo` (banda), `score_riesgo` (nivel), un dato de comunidad de la colonia (nombre y tipo) y `por_que` (frase que explique el orden en términos de las prioridades del usuario).
10. CUANDO ningún anuncio cumpla los filtros, LA herramienta DEBE devolver lista vacía, indicar qué filtro eliminó más anuncios y sugerir cuál relajar (presupuesto, tiempo de traslado, aval).
11. EL orden DEBE ser determinista: ante empate de puntuación, se desempata por `id` ascendente.
12. LA herramienta NO DEBE contactar caseros ni ejecutar acciones a nombre del usuario.

### R4. Herramienta `costo_real(inmueble_id, perfil)`
**Historia:** Como usuario, quiero ver cuánto cuesta realmente vivir ahí, no solo la renta.
1. LA herramienta DEBE devolver el desglose mensual de la spec 03: renta o mensualidad de compra, transporte, tiempo de traslado valorizado, servicios y total.
2. CUANDO el inmueble sea de venta, LA herramienta DEBE incluir la mensualidad estimada con la tasa de referencia y el enganche del Perfil, y el aviso "Estimación de mensualidad, no es asesoría hipotecaria."
3. CUANDO el `inmueble_id` no exista, LA herramienta DEBE devolver error con hasta 3 ids parecidos, sin lanzar excepción.
4. LA `explicacion` DEBE nombrar los supuestos usados (modo de transporte, factor de rodeo, velocidad, ingreso por hora, tasa) con su valor.
5. LA herramienta DEBE incluir en `fuentes` las tarifas SEMOVI y la tasa Banxico (con fecha) cuando se usen.

### R5. Herramienta `precio_justo(inmueble_id)`
**Historia:** Como usuario, quiero saber si el precio es razonable para la colonia.
1. LA herramienta DEBE devolver precio por m², mediana de la colonia, razón (precio/mediana) y banda `justo`, `caro` o `sospechosamente_barato`, con los umbrales de la spec 03.
2. CUANDO falte `m2` o la mediana, LA herramienta DEBE devolver la banda `sin_dato` con el motivo.
3. LA `explicacion` DEBE citar la mediana y el origen declarado (por ejemplo, "mediana de anuncios capturados, Roma Norte, 2025-05-10") y, si la mediana proviene de pocos anuncios reales, DEBE avisarlo.
4. CUANDO la banda sea `sospechosamente_barato`, LA `explicacion` DEBE remitir a `score_fraude` en vez de afirmar que es riesgoso.

### R6. Herramienta `score_fraude(inmueble_id)`
**Historia:** Como usuario, quiero saber si el anuncio es confiable, explicado en palabras simples.
1. LA herramienta DEBE devolver el `ResultadoAntifraude` de la spec 04: `score_riesgo` 0-100, `nivel`, `senales` con `evidencia` y `explicacion`, `no_evaluables`, `resumen` y `recomendacion`.
2. EL Servidor NO DEBE usar ni exponer `es_fraude_prueba` en ninguna respuesta de las herramientas de usuario, para no filtrar la etiqueta de prueba.
3. CUANDO `nivel` sea `bajo` sin señales, LA `explicacion` DEBE incluir que esto no garantiza que el anuncio sea real.
4. LOS números de teléfono DEBEN aparecer ocultos parcialmente, igual que en la spec 04.

### R7. Herramienta `info_colonia(colonia)`
**Historia:** Como usuario, quiero conocer la colonia y cómo integrarme a ella.
1. LA herramienta DEBE aceptar el nombre de la colonia sin importar mayúsculas ni acentos (misma normalización de la spec 01) y DEBE resolver coincidencias parciales únicas.
2. CUANDO el nombre sea ambiguo o no exista, LA herramienta DEBE devolver la lista de las 13 colonias piloto disponibles.
3. LA herramienta DEBE devolver: alcaldía, medianas de precio por m² (renta y venta), índice de delitos, estaciones de transporte cercanas con distancia, nivel de riesgo (sísmico e inundación), indicador de presión de gentrificación y puntos de comunidad (mercados, parques, centros culturales).
4. CADA campo DEBE ir con su `fuente` y `fecha_dato`; los campos vacíos DEBEN listarse como "sin dato".
5. LA `explicacion` DEBE incluir al menos una sugerencia concreta de integración basada en los `puntos_comunidad` (por ejemplo, un mercado o parque por su nombre); CUANDO no haya puntos de comunidad, DEBE decirlo.
6. CUANDO el indicador de presión de gentrificación sea alto (>= 0.66), LA `explicacion` DEBE decirlo en lenguaje sencillo y remitir a `alternativas_equilibradas`.

### R8. Herramienta `alternativas_equilibradas(perfil, colonia_origen)`
**Historia:** Como persona que se reubica, quiero opciones que me sirvan sin presionar más a una colonia ya muy presionada.
1. LA herramienta DEBE recibir un Perfil y, opcionalmente, la colonia que el usuario tenía en mente (`colonia_origen`).
2. LA herramienta DEBE devolver hasta 3 alternativas en colonias con presión de gentrificación menor que la de `colonia_origen` (o menor a 0.66 si no se indicó), que cumplan los filtros duros de R3 (presupuesto, operación, recámaras, tiempo de traslado, riesgo no alto).
3. CADA alternativa DEBE incluir la comparación contra la colonia de origen: diferencia en costo real mensual, en minutos de traslado, en índice de delitos y en presión de gentrificación.
4. LA herramienta DEBE preferir, entre colonias con puntuación similar (diferencia <= 5 puntos), la de menor presión de gentrificación.
5. LA `explicacion` DEBE decir de forma respetuosa por qué importa la presión sobre la colonia (precios que suben para residentes de toda la vida) sin culpar al usuario ni afirmar causalidad que los datos no demuestran.
6. CUANDO no haya alternativas, LA herramienta DEBE decirlo y NO DEBE rellenar con colonias que no cumplan los filtros.
7. CUANDO la colonia de origen no sea de alta presión, LA herramienta DEBE decirlo y devolver igualmente las mejores alternativas.

### R9. Reglas transversales del agente
**Historia:** Como jurado, quiero ver que el agente es honesto y no inventa.
1. EL Servidor DEBE exponer a Kiro una instrucción de sistema (`instructions` de FastMCP) que indique: recomendar sin ejecutar acciones, citar fuentes, decir cuando no hay datos, avisar sintético y ubicación aproximada, tono claro y cercano.
2. EL repositorio DEBE incluir una guía de steering (`.kiro/steering/agente.md`) con las mismas reglas para que Kiro las siga en el chat de la demo.
3. LAS herramientas DEBEN ser de solo lectura y estar anotadas como tales (`readOnlyHint`).
4. CUANDO el usuario pida algo fuera de alcance (contactar al casero, pagos, contratos), LA `explicacion` de las herramientas NO DEBE sugerirlo; el steering DEBE indicar a Kiro que lo rechace.

### R10. Rendimiento y pruebas
1. CADA herramienta DEBE responder en menos de 2 s con el dataset completo (~300 anuncios) usando datos en memoria, sin llamadas de red, salvo la geocodificación del destino (con caché).
2. CUANDO falle una fuente externa (Nominatim, Banxico), EL Servidor DEBE usar el último valor en caché o el valor de respaldo documentado en la spec 03 y agregar un aviso; NO DEBE fallar la herramienta.
3. LAS pruebas DEBEN poder ejecutarse sin red ni tokens, con datos de ejemplo pequeños.
4. LAS pruebas DEBEN cubrir las seis herramientas llamándolas como funciones y a través del cliente MCP en memoria.

### R11. Demo
1. EL repositorio DEBE incluir un guion de demo (`docs/demo_agente.md`) con 3 perfiles de ejemplo, los mensajes que se dicen en el chat de Kiro, las herramientas esperadas y qué debe verse en cada respuesta.
2. LOS 3 perfiles DEBEN cubrir: renta con prioridad de precio, compra con prioridad de seguridad y comunidad, y un caso que pida zona de alta presión y active `alternativas_equilibradas`.
3. LOS perfiles DEBEN guardarse como JSON válido contra `Perfil` en `data/raw/demo_perfiles.json`.
4. EL guion DEBE incluir un plan B si Kiro no puede conectar al servidor o falla la red.

## Fuera de alcance
- Front, mapas o cualquier interfaz distinta del chat de Kiro.
- Llamadas a un LLM desde el código; autenticación; despliegue remoto (solo `stdio` local).
- Contactar caseros, pagos, contratos, asesoría legal o financiera vinculante.
- Scraping de portales.
- Escritura de datos o memoria de sesión entre conversaciones.
