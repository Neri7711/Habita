# Diseño — Spec 05: Agente MCP

## Decisiones clave
| Tema | Decisión | Por qué |
|---|---|---|
| LLM | Ninguno en el código; Kiro conversa y llama herramientas | No hay API key; créditos de Kiro (tech.md) |
| Framework | `mcp` con `FastMCP` (`from mcp.server.fastmcp import FastMCP`) | Esquemas de herramientas salen de las anotaciones de tipo y Pydantic |
| Transporte | `stdio` | Kiro lo lanza como proceso hijo; sin puertos ni cuentas |
| Datos | Se cargan una vez a memoria desde `data/processed/*.json` | ~300 anuncios, 13 colonias; respuesta < 2 s sin base de datos |
| Capas | `mcp_server.py` delgado + `arraigo/agente/` con la lógica | Los scripts y herramientas solo llaman funciones; las funciones se prueban sin MCP |
| Respuesta | Envoltorio único `datos / explicacion / fuentes / avisos` | Kiro siempre sabe dónde está la explicación y los avisos |
| Explicación | Texto armado por plantillas en código a partir de números reales | Kiro redacta, pero cada cifra viene de código determinista |
| Ranking | Suma ponderada de criterios normalizados 0-1, pesos por orden de prioridades | Explicable: se puede mostrar el aporte de cada prioridad |
| Solo lectura | Ninguna herramienta escribe ni actúa | Principio del producto: solo recomienda |
| Etiqueta de prueba | `es_fraude_prueba` nunca sale en una respuesta | Evita filtrar la respuesta de la evaluación |

## Estructura
```
src/arraigo/
├── mcp_server.py          # FastMCP: registra herramientas, instructions, main()
└── agente/
    ├── __init__.py
    ├── contexto.py        # ContextoAgente: inmuebles, colonias, config antifraude; cargar_contexto()
    ├── envoltorio.py      # Envoltorio, Fuente, helpers de avisos y errores
    ├── ranking.py         # filtros duros, criterios 0-1, pesos, puntuar()
    ├── explicaciones.py   # plantillas de texto en español sencillo
    └── herramientas.py    # una función pura por herramienta: (ctx, args) -> Envoltorio
tests/
├── test_agente_ranking.py
├── test_agente_herramientas.py
└── test_mcp_server.py
docs/demo_agente.md
data/raw/demo_perfiles.json
.kiro/steering/agente.md
```
`mcp_server.py` solo traduce: valida argumentos, llama a `herramientas.py` y devuelve el Envoltorio. Cero lógica de negocio ahí.

## Dependencias entre specs (contrato esperado)
El servidor consume estas funciones. Los nombres de la spec 03 son el contrato esperado; al implementar, se ajustan los adaptadores
de `herramientas.py` a lo que defina la spec 03 y no se duplica su lógica.

| Spec | Función usada | Entrada → salida |
|---|---|---|
| 01 | `Inmueble`, `Perfil`, `Colonia` | Esquemas; carga de `inmuebles.json` y `colonias.json` con `model_validate` |
| 02 | Campos de `Colonia` | `indice_delitos`, `estaciones_transporte_cercanas`, `nivel_riesgo`, `indicador_presion_gentrificacion`, `puntos_comunidad` (todos `Dato[...]`) |
| 03 | `arraigo.calculos.costo_real(inmueble, perfil, colonia)` | → desglose mensual: renta/mensualidad, transporte, tiempo valorizado, servicios, total, minutos de traslado, supuestos, fuentes |
| 03 | `arraigo.calculos.precio_justo(inmueble, colonia)` | → precio/m², mediana, razón, banda (`justo`/`caro`/`sospechosamente_barato`/`sin_dato`), fuente |
| 04 | `arraigo.antifraude.score.evaluar_anuncio(inmueble, contexto)` | → `ResultadoAntifraude` |
| 04 | `ContextoAntifraude` | Se construye una vez en `cargar_contexto()` con `medianas_m2`, índice de duplicados y `antifraude_reglas.json` |

Si una función de la spec 03 o 04 aún no existe cuando se implementa esta spec, la tarea correspondiente queda bloqueada; no se reimplementa aquí.

## Contexto del agente
```python
class ContextoAgente(BaseModel):
    inmuebles: dict[str, Inmueble]            # por id
    colonias: dict[str, Colonia]              # por nombre normalizado
    nombres_colonia: dict[str, str]           # normalizado -> nombre oficial
    antifraude: ContextoAntifraude
    resultados_antifraude: dict[str, ResultadoAntifraude]   # precalculado al cargar (es_fraude_prueba no se usa)
    generado_en: date
```
- `cargar_contexto(ruta_processed: Path) -> ContextoAgente`. Falta de archivos → `ErrorDatos` con el comando para generarlos.
- Se precalcula el score de todos los anuncios al iniciar (≈300 × reglas puras, milisegundos).
- El contexto se inyecta a las funciones; los tests usan un contexto pequeño armado a mano.

## Envoltorio
```python
class Fuente(BaseModel):
    descripcion: str              # "Mediana de anuncios capturados, Roma Norte"
    fecha_dato: date | None

class Envoltorio(BaseModel):
    ok: bool = True
    datos: dict | list | None
    explicacion: str
    fuentes: list[Fuente] = []
    avisos: list[str] = []
    error: str | None = None      # solo si ok = False; mensaje en español con el campo y el motivo
```
Avisos fijos (constantes en `envoltorio.py`):
- `AVISO_SINTETICO` = "Este anuncio es de ejemplo (sintético), no es una oferta real."
- `AVISO_UBICACION` = "La ubicación es aproximada (centro de la colonia), no la dirección del inmueble."
- `AVISO_HIPOTECA` = "Estimación de mensualidad, no es asesoría hipotecaria."
- `AVISO_SIN_DATO(campo, sujeto)` = "No hay dato de {campo} para {sujeto}."
- Se deduplican por texto cuando una lista de resultados repite el mismo aviso.

## Herramientas
Todas con `@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))` y docstring en español que Kiro lee para decidir cuándo usarlas.

| Herramienta | Argumentos | Datos devueltos |
|---|---|---|
| `buscar_inmuebles` | `perfil: Perfil`, `limite: int = 5` | `resultados[]` (inmueble, puntuacion, desglose, costo_real, precio_justo, riesgo, comunidad, por_que), `total_candidatos`, `excluidos_por_riesgo`, `filtros_aplicados` |
| `costo_real` | `inmueble_id: str`, `perfil: Perfil` | desglose mensual y supuestos de spec 03 |
| `precio_justo` | `inmueble_id: str` | precio/m², mediana, razón, banda |
| `score_fraude` | `inmueble_id: str` | `ResultadoAntifraude` sin `es_fraude_prueba` |
| `info_colonia` | `colonia: str` | ficha con cada campo `{valor, fuente, fecha_dato}` |
| `alternativas_equilibradas` | `perfil: Perfil`, `colonia_origen: str | None` | `alternativas[]` (máx. 3) con `comparacion_con_origen` |

### `buscar_inmuebles`: algoritmo
```
1. candidatos = inmuebles filtrados por operación, precio, recámaras, mascotas, aval        (filtros duros, R3.2-3)
2. para cada candidato: costo_real (spec 03) → minutos de traslado; descartar si > tiempo_max   (R3.4)
3. score_riesgo (precalculado); descartar nivel "alto"; contar descartados                      (R3.5)
4. criterios 0-1 por candidato (ver tabla)
5. puntuacion = 100 × Σ peso_i × criterio_i
6. ordenar por (-puntuacion, id); tomar `limite`
7. armar por_que con las 2 prioridades de mayor aporte
```
Si `operacion_deseada = "ambas"`, el costo real de renta y de compra se calcula por separado y cada anuncio compite con el criterio de precio normalizado dentro de su propia operación (para no comparar renta contra mensualidad de compra de forma injusta).

### Criterios (normalizados 0-1 sobre el conjunto de candidatos de la misma operación)
| Prioridad | Medida | Normalización |
|---|---|---|
| `precio` | `costo_real.total_mensual` | min-max invertido (menor = 1) |
| `traslado` | minutos de traslado | min-max invertido |
| `seguridad` | `colonia.indice_delitos` | min-max invertido sobre las 13 colonias |
| `comunidad` | `len(puntos_comunidad) + len(estaciones)` | min-max sobre las 13 colonias |
| `espacio` | `m2` | min-max sobre candidatos |
- Si `max == min`, el criterio vale 0.5 para todos.
- Dato faltante → 0.5 y aviso por anuncio (R3.8).
- Se usan colonias en la normalización de `seguridad` y `comunidad` para que el valor tenga el mismo significado en cualquier búsqueda.

### Pesos
Pesos base por posición: `[0.35, 0.25, 0.20, 0.12, 0.08]`. Con `n` prioridades se toman los primeros `n` y se reescalan para sumar 1.
Ejemplo con 3 prioridades: `0.35, 0.25, 0.20` → `0.4375, 0.3125, 0.25`.
Las prioridades que el usuario no marca pesan 0 (no se ordena por ellas).

### `por_que` (plantilla)
"Quedó en el lugar {n} porque {p1} y {p2}, que son tus prioridades principales." con frases por criterio, por ejemplo:
- precio: "cuesta en total {X} al mes con transporte y tiempo, menos que la mayoría"
- traslado: "llegas al trabajo en unos {M} minutos"
- seguridad: "la colonia tiene pocos reportes de delitos comparada con las demás"
- comunidad: "tiene {N} lugares de comunidad cerca, como {nombre}"
- espacio: "tiene {m2} m²"
Las comparaciones ("menos que la mayoría") se calculan con el percentil real del criterio; nunca se escriben sin respaldo numérico.

### `alternativas_equilibradas`: algoritmo
```
1. origen = colonia_origen resuelta (o None); umbral = presion(origen) si existe, si no 0.66
2. colonias_candidatas = colonias con presion < umbral (presion nula → excluida y se avisa)
3. correr el ranking de buscar_inmuebles solo sobre inmuebles de esas colonias
4. por colonia, quedarse con el mejor anuncio; ordenar por puntuacion; empate (≤ 5 pts) → menor presion primero
5. top 3; comparacion_con_origen = diferencias vs el mejor anuncio comparable en la colonia de origen
   (mismo filtro, misma operación); si origen no tiene anuncios válidos, solo se comparan las medianas de la colonia
```
- La explicación usa un texto fijo y verificable: "{origen} tiene una presión alta: los precios y la demanda han subido y eso puede
  desplazar a vecinos de toda la vida. {alternativa} cumple lo que buscas con menos presión." Sin atribuir causas al usuario.
- Colonias con `rol = alternativa` en `colonias_piloto.csv` no se priorizan por el rol; el criterio es solo el indicador numérico.

### `info_colonia`
- Resolución: normalizar (minúsculas, sin acentos, sin "col."); coincidencia exacta; si no, coincidencia por prefijo/subcadena única; si hay 0 o varias → lista de las colonias piloto en `datos.colonias_disponibles`.
- Sugerencia de integración (plantilla): "Para conocer la colonia, puedes empezar por {mercado/parque más cercano por nombre}." Se elige el primer punto de tipo `mercado`, luego `parque`, luego `centro_cultural`.
- Presión ≥ 0.66 → "Esta colonia está bajo fuerte presión de gentrificación. Puedes ver opciones más equilibradas con `alternativas_equilibradas`."

## Reglas de seguridad y honestidad
- Entradas se validan con Pydantic en la frontera de la herramienta; los errores se devuelven como `Envoltorio(ok=False, error=...)`.
- `inmueble_id` y `colonia` son datos de usuario: solo se usan como llaves de diccionario, nunca en rutas, shell ni consultas.
- Se eliminan `es_fraude_prueba` y `url_origen` vacía de las salidas; el teléfono se oculta como lo define la spec 04.
- Red: solo la geocodificación del destino y la tasa Banxico (spec 03), ambas con caché y respaldo. Cualquier fallo → aviso, no excepción.
- `stdout` queda reservado al protocolo; `logging` se configura a `stderr` en `main()`.

## `instructions` del servidor (FastMCP)
Texto corto, en español, igual a la guía de `.kiro/steering/agente.md`:
1. Eres un asesor que solo recomienda. No contactas caseros, no pagas, no firmas, no das asesoría legal ni financiera.
2. Para recomendar, usa las herramientas; no inventes precios, inmuebles ni datos de colonias.
3. Cita la fuente y la fecha de cada dato importante. Si falta un dato, dilo.
4. Muestra siempre los avisos (sintético, ubicación aproximada, estimación hipotecaria).
5. Habla de "señales de riesgo", nunca acuses de estafa.
6. Para cada opción, muestra costo real, precio justo, nivel de confianza y un dato de comunidad.
7. Si la colonia tiene alta presión de gentrificación, ofrece alternativas equilibradas.
8. Tono claro y cercano, sin jerga inmobiliaria.

## Registro en `.kiro/settings/mcp.json`
Se crea (o se fusiona, sin borrar otros servidores) en la tarea de registro:
```json
{
  "mcpServers": {
    "arraigo": {
      "command": "uv",
      "args": ["run", "python", "-m", "arraigo.mcp_server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": [
        "buscar_inmuebles", "costo_real", "precio_justo",
        "score_fraude", "info_colonia", "alternativas_equilibradas"
      ]
    }
  }
}
```
- `autoApprove` es seguro porque todas las herramientas son de solo lectura; evita pedir permiso en cada paso de la demo.
- No se escriben tokens. `INEGI_TOKEN` y `BANXICO_TOKEN` se heredan del entorno del usuario.
- Si Kiro no resuelve `${workspaceFolder}`, la tarea de registro usa la ruta absoluta del repo en la máquina de la demo (no se sube a git).
- Antes de editar, se lee el archivo existente (workspace y `~/.kiro/settings/mcp.json`) para no pisar configuración.

## Guion de demo (`docs/demo_agente.md`) y perfiles
Estructura del guion: preparación (comandos y verificación de conexión), para cada perfil el mensaje al chat, las herramientas esperadas, lo que debe verse, y plan B.

| # | Perfil | Mensaje de ejemplo | Herramientas esperadas | Debe verse |
|---|---|---|---|---|
| 1 | **Ana**, 28, ingeniera, se muda desde Monterrey. Renta, presupuesto $18,000, ingreso $45,000, trabaja en Polanco, transporte público, 40 min máx., prioridades: precio, traslado | "Me mudo a CDMX por trabajo y quiero rentar cerca de Polanco, máximo $18,000." | `buscar_inmuebles`, luego `costo_real` y `precio_justo` del primero | Top 3-5 ordenado por precio y traslado, costo total vs. solo renta, banda de precio, aviso de sintético |
| 2 | **Luis y Marta**, pareja con un hijo, compra. Presupuesto $3,200,000, enganche $640,000, ingreso $70,000, trabajo en Santa Fe → modo `auto`, 60 min, 2 recámaras mínimo, mascotas, prioridades: seguridad, comunidad, espacio | "Queremos comprar un depto de 2 recámaras, con mascota, y que sea una colonia tranquila." | `buscar_inmuebles`, `info_colonia`, `score_fraude` | Mensualidad estimada con tasa Banxico y aviso hipotecario, índice de delitos, mercado o parque por nombre, nivel de confianza |
| 3 | **Diego**, 33, desde Guadalajara, quiere Roma Norte. Renta, $22,000, ingreso $60,000, trabajo en Reforma, bici/mixto, 35 min, prioridades: comunidad, traslado, precio | "Me encantaría vivir en la Roma Norte. ¿Me conviene?" | `info_colonia` (Roma Norte), `alternativas_equilibradas`, `costo_real` comparativo | Aviso de alta presión en lenguaje respetuoso; hasta 3 colonias con diferencias en costo, traslado, delitos y presión |

- Los perfiles se guardan en `data/raw/demo_perfiles.json` (lista de objetos `Perfil` válidos) y una prueba los valida con el esquema.
- Coordenadas de los destinos (Polanco, Santa Fe, Reforma): ubicaciones aproximadas fijas en el JSON, para que la demo no dependa de geocodificación en vivo.
- Plan B: el guion trae, por perfil, las respuestas reales de las herramientas capturadas en un bloque de texto (generadas llamando las funciones de `herramientas.py` desde `scripts/capturar_demo.py`), para narrarlas si falla la conexión. Verificación previa: `uv run python -m arraigo.mcp_server` arranca sin error y Kiro lista las seis herramientas en el panel MCP.
- La demo avisa en voz alta que los anuncios son sintéticos y que la ubicación es aproximada.

## Pruebas
- `test_agente_ranking.py`: pesos suman 1 para n = 1..5; primera prioridad pesa más; criterio con `max == min` → 0.5; dato faltante → 0.5 con aviso; desempate por id; determinismo (dos corridas iguales).
- `test_agente_herramientas.py` (contexto pequeño a mano, sin red):
  - `buscar_inmuebles`: respeta cada filtro duro; excluye riesgo alto y lo cuenta; aval; mascotas; lista vacía sugiere filtro a relajar.
  - Envoltorio: sintético → aviso; ubicación aproximada → aviso; dato faltante → `null` y aviso, nunca valor inventado.
  - `precio_justo`: bandas y `sin_dato` sin `m2`.
  - `score_fraude`: no aparece `es_fraude_prueba`; sin señales → "no garantiza".
  - `info_colonia`: acentos y mayúsculas; ambigua → lista; incluye sugerencia de integración.
  - `alternativas_equilibradas`: todas con presión menor al origen; máx. 3; sin alternativas → mensaje sin relleno.
  - Ninguna salida contiene "estafa".
- `test_mcp_server.py`: con el cliente en memoria del paquete `mcp` (`create_connected_server_and_client_session`), listar herramientas (6), llamar cada una con datos de ejemplo, verificar `readOnlyHint` y que `instructions` no esté vacío.
- `test_demo_perfiles.py`: `demo_perfiles.json` valida contra `Perfil` y trae 3 perfiles; cada uno devuelve ≥ 1 resultado con el dataset real si existe `data/processed/inmuebles.json` (si no, se omite).
- Prueba manual: conectar Kiro y correr los 3 mensajes del guion.
