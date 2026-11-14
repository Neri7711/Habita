# Spec 02: Enriquecimiento de colonias

## Introducción

Llenar con datos abiertos los campos de contexto del esquema `Colonia` que la spec 01 dejó en `null`:
`indice_delitos`, `estaciones_transporte_cercanas`, `nivel_riesgo`, `puntos_comunidad` e `indicador_presion_gentrificacion`.
El alcance son las 13 colonias piloto (`data/raw/colonias_piloto.csv`). Esta spec **no incluye LLM, interfaz ni scraping**.
Usa los clientes que ya existen en `src/arraigo/fuentes/` (estado en `data/raw/FUENTES.md`) y no agrega llamadas HTTP nuevas por fuera de ellos.

## Supuestos y dependencias

- La spec 01 está terminada: existen `schemas/colonia.py` (con `Dato[T]`, `Punto`, `Estacion`, `NivelRiesgo`, `PuntoComunidad`),
  `pipeline/colonias.py` (centroides y polígonos del catálogo oficial) y `data/processed/colonias.json`.
- Tokens gratuitos en variables de entorno: `INEGI_TOKEN` (DENUE). `BANXICO_TOKEN` no se usa en esta spec.
- Los campos internos de `Estacion`, `NivelRiesgo` y `PuntoComunidad` se precisan en `design.md`. Si la spec 01 los dejó más pobres, se amplía `colonia.py` como tarea explícita (tarea 1.1).
- El indicador de gentrificación es una **heurística transparente**, no una medición validada. El agente debe presentarlo así.

## Requerimientos

### R1. Índice de delitos
**Historia:** Como agente, necesito un nivel de incidencia delictiva comparable entre colonias para ponderar la prioridad "seguridad".

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular `indice_delitos` (0-1) por colonia a partir de las carpetas de investigación de la FGJ publicadas en Datos Abiertos CDMX, usando `arraigo.fuentes.datos_cdmx`.
2. EL SISTEMA DEBERÁ contar solo carpetas de los últimos 12 meses completos disponibles en el dataset, con coordenadas válidas dentro de CDMX, y asignarlas a la colonia por punto en polígono del catálogo oficial.
3. EL SISTEMA DEBERÁ normalizar el conteo (por 1,000 habitantes del Censo 2020 cuando haya población; si no, por km²) a 0-1 con rango percentil contra todas las colonias del catálogo, no solo las piloto.
4. EL SISTEMA DEBERÁ guardar `fuente` (nombre del dataset y organización) y `fecha_dato` (fecha de corte o de última modificación del recurso).
5. SI el dataset no responde o no trae coordenadas, ENTONCES EL SISTEMA DEBERÁ dejar `valor = null` y registrar el motivo, sin inventar un valor.
6. EL SISTEMA DEBERÁ documentar en el resultado que el índice mide delitos **registrados**, que subestima los no denunciados.

### R2. Transporte cercano
**Historia:** Como agente, necesito saber qué estaciones hay cerca de cada colonia para estimar traslados y costo de transporte (spec 03).

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ listar, por colonia, las estaciones de transporte a 800 m o menos del centroide, con: nombre, modo (metro, metrobus, tren_ligero, cablebus, trolebus, ecobici), lat, lng y distancia en metros.
2. EL SISTEMA DEBERÁ obtener estaciones de Metro, Metrobús, Tren Ligero, Cablebús y Trolebús del GTFS de SEMOVI publicado en Datos Abiertos CDMX, y estaciones Ecobici de su feed público de estaciones.
3. SI el GTFS no está disponible, ENTONCES EL SISTEMA DEBERÁ usar la categoría `estacion_transporte` de `arraigo.fuentes.overpass` como respaldo y marcarlo en `fuente`.
4. EL SISTEMA DEBERÁ eliminar duplicados (misma estación y modo a menos de 50 m) y ordenar por distancia.
5. EL SISTEMA DEBERÁ guardar `fuente` y `fecha_dato` (fecha de publicación del GTFS o de la consulta del feed).
6. UNA colonia sin estaciones en el radio DEBERÁ quedar con lista vacía (dato válido), distinta de `null` (dato no obtenido).

### R3. Nivel de riesgo
**Historia:** Como agente, necesito avisar riesgos sísmicos y de inundación de la zona en lenguaje simple.

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ asignar a cada colonia un nivel `bajo | medio | alto` para riesgo `sismico` y para `inundacion`, usando las capas del Atlas de Riesgos de la CDMX publicadas en Datos Abiertos CDMX.
2. EL SISTEMA DEBERÁ evaluar la capa sobre el polígono de la colonia (clase que cubre más área) y, si hay varias, conservar la de mayor nivel como `nivel` y la de mayor área como `clase_dominante`.
3. EL SISTEMA DEBERÁ guardar el nombre de la capa usada, `fuente` y `fecha_dato`.
4. SI no se encuentra una capa utilizable en el portal, ENTONCES EL SISTEMA DEBERÁ dejar `nivel_riesgo.valor = null`, registrar el motivo y marcar la tarea como bloqueada para decisión humana (descarga manual a `data/raw/`).
5. EL texto de explicación DEBERÁ indicar que es un nivel de zona y no un dictamen sobre un inmueble específico.

### R4. Puntos de comunidad
**Historia:** Como agente, necesito datos concretos de la colonia (mercados, parques, cultura, comercio local) para explicar el encaje con la comunidad.

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ obtener, con `arraigo.fuentes.overpass.puntos_cercanos` a 800 m del centroide, los puntos de categorías `mercado`, `parque` y `centro_cultural`, con nombre cuando exista.
2. EL SISTEMA DEBERÁ complementar con `arraigo.fuentes.inegi_denue.negocios_cercanos` (radio 500 m) el conteo de comercio local de barrio (por ejemplo mercados, tianguis, abarrotes, fondas, papelerías) y guardarlo como resumen por tipo, no como lista completa.
3. EL SISTEMA DEBERÁ respetar los límites de las fuentes: 1 petición por segundo a Overpass con espejos de respaldo, y caché en disco de `_http.py`.
4. SI falta `INEGI_TOKEN`, ENTONCES EL SISTEMA DEBERÁ continuar solo con OpenStreetMap, marcarlo en `fuente` y avisar con un mensaje claro (nunca imprimir el token).
5. EL SISTEMA DEBERÁ guardar `fuente` (ambas, si aplica) y `fecha_dato` (fecha de la consulta, porque OSM y DENUE no tienen corte fijo).
6. CADA colonia piloto DEBERÍA tener al menos un punto de comunidad; si no, el reporte DEBERÁ señalarlo.

### R5. Indicador de presión de gentrificación
**Historia:** Como agente, necesito señalar cuándo una zona está bajo fuerte presión de gentrificación y sugerir alternativas (principio de reubicación consciente).

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular `indicador_presion_gentrificacion` (0-1) combinando tres componentes, con la fórmula y pesos documentados en `design.md`:
   densidad de anuncios Inside Airbnb por km², cambio 2010-2020 en la proporción de población adulta con educación superior, y cambio 2010-2020 en la población residente. Los dos últimos vienen del Censo INEGI por AGEB.
2. EL SISTEMA DEBERÁ descargar el CSV de Inside Airbnb con `arraigo.fuentes.inside_airbnb.descargar_listings` y asignar cada anuncio a una colonia por punto en polígono.
3. EL SISTEMA DEBERÁ agregar los datos de AGEB a colonia asignando cada AGEB a la colonia que contiene su centroide, y declarar esa aproximación.
4. EL SISTEMA DEBERÁ normalizar cada componente a 0-1 por rango percentil contra todas las colonias del catálogo con datos.
5. EL SISTEMA DEBERÁ guardar también los componentes individuales (no solo el total) para poder explicar el resultado en lenguaje simple.
6. EL SISTEMA DEBERÁ registrar `fuente` (Inside Airbnb con su fecha de corte, y Censo INEGI 2010 y 2020) y `fecha_dato` (la del corte de Airbnb).
7. SI falta un componente, ENTONCES EL SISTEMA DEBERÁ recalcular con los pesos restantes reescalados y marcar `componentes_faltantes`; SI faltan todos, `valor = null`.
8. EL SISTEMA DEBERÁ comparar el resultado con `hipotesis_presion` de `colonias_piloto.csv` en el reporte, sin modificar la hipótesis. Si el indicador la contradice, se informa tal cual.
9. EL SISTEMA DEBERÁ declarar en la salida que es una heurística: densidad de renta corta y cambio demográfico son indicios indirectos, no prueba de desplazamiento.

### R6. Procedencia y calidad de datos (transversal)
**Criterios de aceptación:**
1. CADA campo enriquecido DEBERÁ llevar `fuente` y `fecha_dato` (convención de `tech.md` y R3.2 de la spec 01). Un `valor` no nulo sin ambos es inválido.
2. EL SISTEMA NO DEBERÁ hacer scraping: solo APIs, datasets descargables y feeds públicos de las fuentes listadas en `data/raw/FUENTES.md`.
3. EL SISTEMA DEBERÁ distinguir "dato no obtenido" (`valor = null`) de "dato obtenido y vacío" (lista vacía o conteo 0).
4. EL SISTEMA DEBERÁ ser reejecutable: usar la caché de `_http.py` y no volver a descargar archivos que ya existen en `data/raw/`.
5. LOS tokens DEBERÁN leerse solo de variables de entorno y no escribirse en código, logs ni salidas.
6. TODA fuente nueva o archivo descargado DEBERÁ registrarse en `data/raw/FUENTES.md` con URL, fecha de descarga y licencia.

### R7. Integración y reporte
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ escribir las 13 colonias enriquecidas en `data/processed/colonias.json`, conservando los campos de la spec 01 (nombre, alcaldía, centroide, precios m2) sin alterarlos.
2. EL SISTEMA DEBERÁ generar `data/processed/reporte_enriquecimiento.json` y `.md` con: por campo y colonia, estado (`ok`, `parcial`, `faltante`), fuente, fecha_dato y motivo del faltante.
3. EL reporte DEBERÁ incluir la comparación del indicador de gentrificación contra `hipotesis_presion` (R5.8).
4. EL SISTEMA DEBERÁ permitir ejecutar cada enriquecedor por separado y que el fallo de uno no detenga a los demás.

### R8. Pruebas
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ tener pruebas unitarias con datos de ejemplo pequeños (sin red) para cada cálculo: normalización percentil, punto en polígono, distancia haversine, filtro de 12 meses, fórmula de gentrificación (incluido el caso de componente faltante).
2. EL SISTEMA DEBERÁ tener pruebas de los clientes con respuestas simuladas, no con red real.
3. EL SISTEMA DEBERÁ tener una prueba de integración que verifique que ningún `valor` no nulo carece de `fuente` o `fecha_dato`.
4. EL SISTEMA DEBERÁ tener una prueba que cargue `colonias.json` enriquecido y valide cada colonia con el esquema `Colonia`.
