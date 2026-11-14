# Diseño — Spec 02: Enriquecimiento de colonias

## Decisiones clave

| Tema | Decisión | Por qué |
|---|---|---|
| Alcance geográfico | 13 colonias piloto para consultas por API; catálogo completo (~1,800 colonias) para normalizar | Un percentil solo entre 13 colonias no significa nada |
| Asignación a colonia | Punto en polígono con `shapely` (ya agregado por la spec 01) | Fuente oficial de límites; no depende del texto de colonia de cada dataset, que viene sucio |
| Fuentes | Solo los clientes de `src/arraigo/fuentes/`; descargas grandes con `_http.descargar` a `data/raw/` | `tech.md`: no escribir HTTP nuevo |
| Datos masivos (FGJ, Airbnb, AGEB) | Descargar archivo una vez, procesar con pandas/DuckDB | Evita miles de llamadas a API |
| Datos puntuales (OSM, DENUE) | Consulta por centroide con radio | Pocas llamadas (13 × 1-2), con caché |
| Normalización | Rango percentil 0-1 contra todo el catálogo | Robusto a valores extremos (Centro, Cuauhtémoc) |
| Fallos | Cada enriquecedor es independiente; falla → `valor = null` + motivo | R7.4 |
| Gentrificación | Heurística con fórmula pública, componentes guardados | Explicable al usuario y al jurado; no se vende como medición validada |
| Resultado | Se amplía `data/processed/colonias.json`, sin tocar campos de spec 01 | Mismo contrato para specs 03 y 05 |

## Fuentes y qué cliente usa cada una

| Dato | Fuente | Cliente existente | Archivo o consulta | Token |
|---|---|---|---|---|
| Delitos | FGJ CDMX, carpetas de investigación (Datos Abiertos CDMX) | `datos_cdmx.buscar_datasets("carpetas de investigación FGJ")` + `_http.descargar` | CSV en `data/raw/fgj_carpetas.csv` | No |
| Transporte | GTFS SEMOVI (Datos Abiertos CDMX) | `datos_cdmx.buscar_datasets("GTFS")` + `_http.descargar` | ZIP en `data/raw/gtfs_semovi.zip` (se lee `stops.txt`) | No |
| Ecobici | Feed público de estaciones de Ecobici (GBFS) | `_http.get_json` (URL a confirmar en la tarea 3.1) | Consulta única, caché | No |
| Transporte (respaldo) | OpenStreetMap | `overpass.puntos_cercanos` (categoría `estacion_transporte`) | Por centroide | No |
| Riesgo | Atlas de Riesgos CDMX (Datos Abiertos CDMX) | `datos_cdmx.buscar_datasets("atlas de riesgos")` + `_http.descargar` | GeoJSON/SHP en `data/raw/atlas_*` | No |
| Comunidad | OpenStreetMap | `overpass.puntos_cercanos` (800 m) | Por centroide | No |
| Comunidad | INEGI DENUE | `inegi_denue.negocios_cercanos` (500 m) | Por centroide | `INEGI_TOKEN` |
| Gentrificación (renta corta) | Inside Airbnb, corte 2026-09-23, CC BY 4.0 | `inside_airbnb.descargar_listings` | `data/raw/airbnb_listings_2026-09-23.csv` | No |
| Gentrificación (censo) | INEGI, Censo 2010 y 2020, resultados por AGEB urbana | `_http.descargar` (descarga a mano si el sitio lo exige, ver 6.1) | `data/raw/censo_ageb_2010.csv`, `censo_ageb_2020.csv` | No |
| Población por colonia | Censo 2020 por AGEB (mismo archivo) | — | Se agrega junto con el censo | No |

Riesgos de fuente conocidos:
- Los datasets de FGJ y del Atlas de Riesgos cambian de nombre y formato. La tarea 2.1 y la 4.1 empiezan **buscando y fijando** el dataset exacto (nombre CKAN, id de recurso, formato) y lo anotan en `FUENTES.md`. Si no existe un recurso utilizable, la tarea queda bloqueada y se avisa (R3.4).
- Overpass público da 502 con frecuencia; el cliente ya prueba espejos. El resultado se cachea.
- Si el INEGI solo entrega AGEB por descarga manual, es una tarea de humano (6.1). El resto de la spec no depende de ella, salvo el componente censal de R5.

## Estructura de código

```
src/arraigo/
├── schemas/colonia.py              # (spec 01) se amplía solo si falta algún campo de abajo
├── pipeline/
│   ├── colonias.py                 # (spec 01) centroides y polígonos; se reutiliza
│   └── enriquecer/
│       ├── __init__.py             # enriquecer_todo(), ejecutores por campo
│       ├── geo.py                  # haversine, punto en polígono, asignar_a_colonia
│       ├── normalizar.py           # rango_percentil()
│       ├── delitos.py
│       ├── transporte.py
│       ├── riesgo.py
│       ├── comunidad.py
│       ├── gentrificacion.py
│       └── reporte.py              # reporte_enriquecimiento (json + md)
scripts/enriquecer_colonias.py      # CLI: llama a enriquecer_todo(); sin lógica de negocio
tests/enriquecer/                   # espejo del paquete
```
Reglas: las funciones de cálculo son puras (reciben DataFrames o listas y regresan valores). La lectura de archivos y las llamadas a clientes quedan en funciones `cargar_*` y `obtener_*` separadas, para probar los cálculos sin red.

## Modelos (extensión de `schemas/colonia.py`)

Todo campo sigue siendo `Dato[T]` con `valor`, `fuente` y `fecha_dato`. Se agregan o precisan estos tipos (si la spec 01 ya los tiene iguales, no se cambia nada):

```python
class Modo(str, Enum): metro; metrobus; tren_ligero; cablebus; trolebus; ecobici
class Estacion(BaseModel):
    nombre: str
    modo: Modo
    lat: float; lng: float
    distancia_m: int

class Nivel(str, Enum): bajo; medio; alto
class NivelRiesgo(BaseModel):
    sismico: Nivel
    inundacion: Nivel
    clase_sismico: str | None        # p. ej. "Zona III (lacustre)"
    clase_inundacion: str | None
    capa_sismico: str                # nombre de la capa del Atlas
    capa_inundacion: str

class CategoriaComunidad(str, Enum): mercado; parque; centro_cultural
class PuntoComunidad(BaseModel):
    categoria: CategoriaComunidad
    nombre: str | None
    lat: float; lng: float
    distancia_m: int

class ComercioLocal(BaseModel):    # resumen DENUE
    radio_m: int
    total_negocios: int
    por_tipo: dict[str, int]       # {"abarrotes": 12, "fondas": 5, ...}

class PuntosComunidad(BaseModel):
    puntos: list[PuntoComunidad]
    comercio_local: ComercioLocal | None   # None si no hubo INEGI_TOKEN

class PresionGentrificacion(BaseModel):
    valor: float                     # 0-1
    componentes: dict[str, float | None]   # densidad_airbnb, cambio_educacion, cambio_poblacion (0-1 c/u)
    componentes_faltantes: list[str]
    crudos: dict[str, float | None]  # listings_por_km2, delta_pp_educacion_superior, cambio_pct_poblacion
    es_heuristica: bool = True
```
Los campos de `Colonia` pasan a: `indice_delitos: Dato[IndiceDelitos]` (`valor` 0-1 más `delitos_12m`, `tasa_por_1000_hab` o `por_km2`, `base`), `estaciones_transporte_cercanas: Dato[list[Estacion]]`, `nivel_riesgo: Dato[NivelRiesgo]`, `puntos_comunidad: Dato[PuntosComunidad]`, `indicador_presion_gentrificacion: Dato[PresionGentrificacion]`.

Nota: si el contrato de la spec 01 exige `indice_delitos: Dato[float]`, se mantiene `valor: float` y los datos crudos van en un campo hermano `detalle`. La tarea 1.1 resuelve esto antes de escribir enriquecedores.

## Procedimientos

### Utilidades comunes (`geo.py`, `normalizar.py`)
- `haversine_m(lat1, lng1, lat2, lng2) -> float` (radio terrestre 6,371,008 m).
- `asignar_a_colonia(puntos: DataFrame[lat,lng], poligonos) -> Series[nombre_colonia | NA]`: índice espacial `shapely.STRtree` sobre los polígonos de `pipeline/colonias.py`.
- `area_km2(poligono)`: proyectar a EPSG:32614 (UTM 14N) con `pyproj` para el área. Si no se quiere sumar dependencia, aproximar con factor de grados a metros en lat 19.4 (documentar el error, menor a 1% en CDMX).
- `rango_percentil(valores: Series) -> Series`: `rank(pct=True, method="average")` reescalado a [0, 1]. Con un solo valor distinto, regresa 0.5.

### 1. Delitos (`delitos.py`)
1. Buscar el dataset de carpetas FGJ y elegir el recurso CSV más reciente (por `modificado`). Registrar nombre, id y fecha en `FUENTES.md`.
2. Descargar con `_http.descargar`. Leer solo columnas necesarias (fecha de hechos, delito, categoría, latitud, longitud).
3. Filtrar: fecha dentro de los últimos 12 meses completos del corte; lat/lng dentro de CDMX (19.0-19.6, -99.4 a -98.9); descartar coordenadas (0, 0) y duplicadas.
4. Asignar a colonia por punto en polígono. Contar por colonia: `delitos_12m`.
5. Tasa: `delitos_12m / (poblacion_2020 / 1000)` si hay población por colonia (viene del censo, ver gentrificación); si no, `delitos_12m / area_km2`. Guardar en `base` cuál se usó, igual para todas las colonias.
6. `valor = rango_percentil(tasa)` sobre todas las colonias del catálogo con al menos una población o área válida.
7. `fecha_dato` = fecha máxima de hechos en el archivo filtrado. `fuente` = `"FGJ CDMX, carpetas de investigación (Datos Abiertos CDMX)"`.
8. Limitación declarada: colonias con mucha población flotante (Centro, Juárez) salen infladas si se usa tasa por residente. Se documenta en el reporte; no se corrige.

### 2. Transporte (`transporte.py`)
1. Del GTFS: leer `stops.txt` y, si está, `routes.txt`/`agency.txt` para inferir el modo (por agencia o prefijo de ruta: Metro, Metrobús, STE: Tren Ligero y Trolebús, Cablebús). Si el modo no se puede inferir, se descarta la parada y se cuenta en el reporte.
2. Ecobici: leer estaciones (nombre, lat, lng) del feed GBFS y asignar `modo = ecobici`.
3. Por centroide: filtrar paradas a ≤ 800 m con `haversine_m` (prefiltro por caja de coordenadas para no calcular 10,000+ distancias por colonia).
4. Unir duplicados: mismo nombre normalizado y modo a < 50 m (las paradas GTFS vienen por andén). Conservar el más cercano.
5. Ordenar por `distancia_m` y guardar. `fecha_dato` = fecha de publicación del GTFS (o `modificado` del recurso CKAN); para Ecobici, fecha de consulta. `fuente` lista ambas.
6. Respaldo con `overpass.puntos_cercanos(...)` filtrando `estacion_transporte`; `fuente = "OpenStreetMap / Overpass (ODbL)"` y modo `desconocido` no permitido: si no se puede inferir, se omite.

### 3. Riesgo (`riesgo.py`)
1. Buscar capas del Atlas de Riesgos: zonificación geotécnica (sísmico) y susceptibilidad o peligro por inundación. Fijar nombre y recurso en `FUENTES.md`.
2. Intersectar el polígono de cada colonia con la capa. Por colonia, calcular el área por clase.
3. Mapeo de clase a nivel (tabla en código, documentada, revisable por el equipo):

| Capa | Clase de origen | Nivel |
|---|---|---|
| Sísmico (zona geotécnica) | I (lomas) | bajo |
| Sísmico | II (transición) | medio |
| Sísmico | III (lacustre) | alto |
| Inundación | Según clasificación de la capa (muy bajo/bajo, medio, alto/muy alto) | bajo / medio / alto |

4. `nivel` = máximo entre clases que cubren al menos 20% de la colonia; `clase_*` = clase de mayor área. Si ninguna llega a 20%, se usa la de mayor área.
5. Si la capa viene en otro CRS, reproyectar a WGS84 antes de intersectar. Se registra el CRS original.
6. Si no hay capa utilizable: `valor = null`, motivo en el reporte, tarea bloqueada (R3.4).

### 4. Comunidad (`comunidad.py`)
1. Por centroide: `overpass.puntos_cercanos(lat, lng, 800)`; calcular `distancia_m` y ordenar. Limitar a 15 puntos por categoría (los más cercanos) para mantener el JSON chico.
2. DENUE: `inegi_denue.negocios_cercanos(lat, lng, 500, palabra)` para una lista corta de palabras (`mercado`, `abarrotes`, `fonda`, `papeleria`, `tianguis`). Se cuenta por tipo y se suma sin duplicar por `Id` del negocio. No se guardan nombres ni dirección de negocios.
3. Con `INEGI_TOKEN` ausente: `comercio_local = None` y se anota en `fuente`. No es error.
4. `fecha_dato` = fecha de la consulta (ISO). Para la reproducibilidad se guarda la respuesta en la caché de `_http.py`.
5. Limitación declarada: OSM tiene cobertura desigual. El reporte marca colonias con 0 puntos.

### 5. Presión de gentrificación (`gentrificacion.py`)

**Componentes** (cada uno normalizado a 0-1 con `rango_percentil` entre todas las colonias del catálogo con dato):

| Clave | Qué mide | Cálculo crudo | Dirección |
|---|---|---|---|
| `densidad_airbnb` | Renta corta | `listings_en_colonia / area_km2` (Inside Airbnb, corte 2026-09-23) | más densidad, más presión |
| `cambio_educacion` | Llegada de población con mayor escolaridad | `pct_superior_2020 − pct_superior_2010`, en puntos porcentuales. `pct_superior` = población de 18 años y más con educación posbásica o superior / población de 18 años y más | más aumento, más presión |
| `cambio_poblacion` | Salida de residentes | `(pob_2020 − pob_2010) / pob_2010`, con signo invertido para el índice | más pérdida, más presión |

**Fórmula:**

```
presion = (0.40 * densidad_airbnb + 0.35 * cambio_educacion + 0.25 * cambio_poblacion)
          / suma de pesos de los componentes disponibles
```
- Si falta un componente, se divide entre la suma de los pesos disponibles y se anota en `componentes_faltantes`.
- Si faltan todos, `valor = null`.
- Los pesos son un juicio del equipo, no estimados de datos. Viven en una constante `PESOS` en `gentrificacion.py`, con este mismo texto como docstring.
- `valor` se redondea a 3 decimales.

**Procedimiento:**
1. Airbnb: `inside_airbnb.descargar_listings(data/raw)`, leer `latitude`, `longitude`, `id`; descartar nulos, duplicados por `id` y puntos fuera de CDMX; asignar a colonia; contar.
2. Censo: leer ITER por AGEB 2010 y 2020 (solo AGEB urbanas). Las claves de AGEB cambian entre censos (hay AGEB divididas o fusionadas), así que **no se cruza AGEB contra AGEB**: cada censo se agrega por separado a colonia y se comparan los totales de colonia.
3. Agregación AGEB a colonia: el AGEB se asigna a la colonia que contiene su centroide (requiere el marco geoestadístico de AGEB; se descarga y registra en `FUENTES.md`). Aproximación declarada: un AGEB que cruza dos colonias cuenta completo en una.
4. Los porcentajes se calculan sobre totales sumados (no promedios de porcentajes).
5. Variables del censo: se confirman por nombre de columna en la tarea 5.2, dado que 2010 y 2020 usan nomenclaturas distintas (p. ej. `POBTOT`; población de 18+ con educación posbásica `P18YM_PB` en 2020 y su equivalente en 2010). Si una variable no es comparable entre censos, el componente queda faltante en lugar de aproximarse.
6. `fecha_dato` = `2026-09-23` (corte Airbnb). `fuente` = `"Inside Airbnb, corte 2026-09-23 (CC BY 4.0); INEGI, Censo de Población y Vivienda 2010 y 2020 (AGEB)"`.
7. Comparación con `hipotesis_presion` (R5.8): tabla en el reporte con `hipotesis_presion`, `valor`, y una columna `coincide` (si la hipótesis es alta y el valor ≥ 0.66, o media y 0.33-0.66, o baja y < 0.33). No se corrige ninguno de los dos.

**Texto para el agente** (guardado en `explicacion` del dato): "Estimación orientativa. Combina cuántos anuncios de renta corta hay por km², cuánto subió la escolaridad de sus habitantes y cuánto cambió su población entre 2010 y 2020. Son señales indirectas y no prueban desplazamiento."

### 6. Orquestación (`enriquecer/__init__.py`)
```python
def enriquecer_todo(colonias: list[Colonia], campos: set[str] | None = None) -> tuple[list[Colonia], ReporteEnriquecimiento]:
    ...  # corre cada enriquecedor en try/except; un fallo se anota y continúa
```
- Entrada: `data/processed/colonias.json` de la spec 01. Salida: el mismo archivo con campos nuevos, más `reporte_enriquecimiento.json` y `.md`.
- Se escribe primero a un archivo temporal y luego se reemplaza, y se conserva `colonias.json.bak`. Así no se pierde la salida de la spec 01 si algo falla.
- `scripts/enriquecer_colonias.py [--campos delitos,transporte,...]` solo llama a `enriquecer_todo`.

## Reporte (`reporte_enriquecimiento.md`)
- Tabla colonia × campo con estado `ok | parcial | faltante`.
- Por campo: fuente, `fecha_dato`, número de colonias con dato, motivos de faltantes.
- Tabla de gentrificación: crudos, componentes, valor, `hipotesis_presion`, `coincide`.
- Sección "Limitaciones" con las declaradas arriba (delitos registrados, población flotante, cobertura OSM, aproximación AGEB, pesos de la fórmula).

## Pruebas (`tests/enriquecer/`, sin red)
- `test_geo.py`: haversine entre dos puntos conocidos (tolerancia 1%); punto dentro y fuera de un polígono de juguete.
- `test_normalizar.py`: percentil con empates, con un solo valor y con NaN.
- `test_delitos.py`: DataFrame de 12 filas; filtro de ventana, descarte de (0, 0), conteo por colonia, índice entre 0 y 1.
- `test_transporte.py`: paradas simuladas; radio, fusión de duplicados, orden, lista vacía vs `null`.
- `test_riesgo.py`: polígono de juguete con dos clases; regla del 20%; mapeo de clase a nivel.
- `test_comunidad.py`: respuestas simuladas de Overpass y DENUE; sin `INEGI_TOKEN` queda `comercio_local = None`.
- `test_gentrificacion.py`: fórmula con tres componentes; con uno faltante (pesos reescalados); con todos faltantes (`null`); signo del cambio de población.
- `test_procedencia.py`: recorre `colonias.json` y verifica que ningún `valor` no nulo carezca de `fuente` o `fecha_dato`; valida cada colonia con `Colonia`.
- `test_orquestacion.py`: un enriquecedor que lanza excepción no detiene a los demás y queda en el reporte.
