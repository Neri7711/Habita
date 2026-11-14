# Spec 03: Costo real de vivir y precio justo

## Introducción
Calcular, para cada inmueble y perfil, cuánto cuesta realmente vivir ahí cada mes y si el precio del anuncio es justo.
El costo real suma: renta o mensualidad de compra + transporte + tiempo de traslado valorizado + servicios.
El precio justo compara el precio por m² del anuncio contra la mediana de su colonia.
Todo el cálculo es **determinista**: la misma entrada produce siempre el mismo resultado, sin LLM y sin red dentro de las funciones de cálculo.
Cada monto lleva su fuente, su fecha y los supuestos usados, para que el agente (spec 05) pueda explicarlos.
Esta spec **no incluye interfaz** y no da asesoría financiera vinculante.

Depende de la spec 01 (`Inmueble`, `Perfil`, `Colonia`, `Dato`) y usa datos de la spec 02 cuando existen
(`estaciones_transporte_cercanas`). La referencia de precio por m² es la misma que usa la spec 04 (antifraude).
Las herramientas MCP `costo_real` y `precio_justo` se exponen en la spec 05.

## Glosario
- **Modo**: `transporte_publico`, `auto`, `bici` o `mixto` (campo `Perfil.modo_transporte`).
- **Distancia de ruta**: distancia haversine (línea recta) × factor de rodeo del modo.
- **Mediana de la colonia**: `precio_m2_renta_mediana` o `precio_m2_venta_mediana` de `Colonia`.
- **Razón de precio**: (precio del anuncio ÷ m²) ÷ mediana de la colonia para esa operación.

## Requerimientos

### R1. Traslado estimado
**Historia:** Como usuario que se reubica por trabajo, necesito saber cuánto tardaré y cuánto recorreré entre mi casa y mi trabajo.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular la distancia haversine entre el inmueble (`lat`, `lng`) y el destino de trabajo, en kilómetros.
2. EL SISTEMA DEBERÁ calcular la distancia de ruta como distancia haversine × factor de rodeo del modo.
3. EL SISTEMA DEBERÁ calcular el tiempo de traslado de ida, en minutos enteros, como distancia de ruta ÷ velocidad promedio del modo.
4. EL SISTEMA DEBERÁ leer factores de rodeo y velocidades de una tabla de supuestos con fuente (`data/raw/calculos_supuestos.json`), no del código.
5. CUANDO el modo sea `mixto`, EL SISTEMA DEBERÁ usar los supuestos de `transporte_publico` y avisarlo en el resultado.
6. CUANDO la dirección del destino llegue como texto sin coordenadas, EL SISTEMA DEBERÁ geocodificarla con `arraigo.fuentes.nominatim` (máx. 1 solicitud por segundo, con caché) fuera de las funciones de cálculo.
7. SI Nominatim no encuentra la dirección, ENTONCES EL SISTEMA DEBERÁ devolver un error claro que pida al usuario una dirección más precisa; NO DEBERÁ inventar coordenadas.
8. CUANDO el inmueble tenga `ubicacion_aproximada = true`, EL SISTEMA DEBERÁ incluir el aviso "ubicación aproximada: el traslado puede variar".
9. CUANDO el tiempo de ida supere `Perfil.tiempo_max_traslado_min`, EL SISTEMA DEBERÁ marcar `excede_tiempo_max = true` (el filtrado lo decide la spec 05).
10. SI el inmueble no tiene `lat` o `lng`, ENTONCES EL SISTEMA DEBERÁ rechazar el cálculo de traslado con el motivo "sin ubicación".

### R2. Costo de transporte con tarifas oficiales SEMOVI
**Historia:** Como usuario, quiero saber cuánto gastaré al mes en moverme, con tarifas reales.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ guardar las tarifas oficiales de la Secretaría de Movilidad (SEMOVI) en una **tabla fija** (`data/raw/tarifas_semovi.json`) con: servicio, tarifa en MXN, URL de la fuente y fecha de vigencia.
2. LA tabla DEBERÁ incluir como mínimo Metro, Metrobús, Trolebús, Tren Ligero, RTP, Cablebús y la anualidad de Ecobici.
3. EL SISTEMA DEBERÁ estimar el número de pasajes por viaje según la distancia de ruta (umbrales en la tabla de supuestos).
4. CUANDO el modo sea `transporte_publico` o `mixto`, EL SISTEMA DEBERÁ calcular: pasajes por viaje × tarifa × 2 viajes al día × días laborales al mes.
5. CUANDO la colonia tenga `estaciones_transporte_cercanas` (spec 02), EL SISTEMA DEBERÁ usar la tarifa del tipo de la estación más cercana; si no las tiene, usará la tarifa por defecto de la tabla de supuestos y lo indicará.
6. CUANDO el modo sea `auto`, EL SISTEMA DEBERÁ calcular distancia de ruta × 2 × días laborales × costo por km (combustible y mantenimiento, supuesto documentado) y avisar que no incluye estacionamiento, seguro ni tenencia.
7. CUANDO el modo sea `bici`, EL SISTEMA DEBERÁ usar la anualidad de Ecobici ÷ 12 como costo mensual.
8. SI una tarifa de la tabla no tiene fecha de vigencia, ENTONCES EL SISTEMA DEBERÁ fallar al cargar la tabla.

### R3. Tiempo de traslado valorizado
**Historia:** Como usuario, quiero ver cuánto "cuesta" el tiempo que paso en el camino.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular el ingreso por hora como `ingreso_mensual_mxn` ÷ horas laborales al mes (supuesto: 22 días × 8 horas).
2. EL SISTEMA DEBERÁ calcular las horas de traslado al mes como tiempo de ida × 2 × días laborales al mes ÷ 60.
3. EL SISTEMA DEBERÁ calcular el tiempo valorizado como ingreso por hora × horas de traslado al mes × `factor_valor_tiempo` (supuesto, por defecto 1.0).
4. EL SISTEMA DEBERÁ mostrar siempre las horas de traslado al mes junto al monto, y NO DEBERÁ presentar el tiempo valorizado como un gasto de bolsillo.
5. EL SISTEMA DEBERÁ reportar el costo real **con** y **sin** tiempo valorizado.

### R4. Servicios
**Historia:** Como usuario, quiero una idea de lo que pagaré en luz, agua, gas e internet.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ estimar los servicios mensuales con una fórmula fija (base + monto por recámara) definida en la tabla de supuestos.
2. EL SISTEMA DEBERÁ marcar el monto como `supuesto` con `fuente = "supuesto del equipo"` y su fecha, y mostrar el desglose (luz, agua, gas, internet).
3. CUANDO la operación sea venta, EL SISTEMA DEBERÁ sumar una estimación de mantenimiento y predial como porcentaje anual del precio ÷ 12 (supuesto).
4. EL SISTEMA DEBERÁ indicar que es una estimación, no una cotización.

### R5. Mensualidad de compra
**Historia:** Como usuario que compra, quiero una mensualidad estimada con un crédito, sin que sea asesoría hipotecaria.
**Criterios de aceptación:**
1. CUANDO la operación sea venta, EL SISTEMA DEBERÁ calcular el enganche como `Perfil.enganche_disponible_mxn`, el monto financiado como precio − enganche, y la mensualidad con amortización francesa (cuota fija): `P·i / (1 − (1+i)^−n)`.
2. EL SISTEMA DEBERÁ obtener la tasa de referencia de Banxico con `arraigo.fuentes.banxico` (serie TIIE a 28 días, `SF43783`) y sumarle un diferencial (spread) documentado como supuesto; esa tasa total es la tasa anual del crédito.
3. EL SISTEMA DEBERÁ guardar la tasa obtenida con su fecha en `data/raw/tasa_referencia.json`; la consulta a la red ocurre solo en la capa de carga, y las funciones de cálculo reciben la tasa como parámetro.
4. SI no hay `BANXICO_TOKEN` o la consulta falla, ENTONCES EL SISTEMA DEBERÁ usar la última tasa guardada; si tampoco existe, usará una tasa de respaldo de la tabla de supuestos y avisará "tasa de respaldo, no es dato de Banxico".
5. EL SISTEMA DEBERÁ usar un plazo por defecto de 20 años (supuesto, configurable) y mostrar tasa, plazo, enganche y monto financiado en el resultado.
6. SI el enganche es menor al porcentaje mínimo del precio (supuesto: 10%), ENTONCES EL SISTEMA DEBERÁ incluir el aviso "enganche menor al mínimo habitual; el crédito podría no aprobarse" y calcular de todos modos.
7. SI el enganche es mayor o igual al precio, ENTONCES la mensualidad DEBERÁ ser 0 y el resultado lo indicará.
8. EL SISTEMA DEBERÁ incluir siempre el aviso "Estimación, no es asesoría hipotecaria; no incluye comisiones, seguros ni gastos de escrituración".
9. EL SISTEMA DEBERÁ indicar si el pago mensual supera el 35% del ingreso mensual (`pago_excede_ingreso`), como referencia general y no como regla de aprobación.

### R6. Costo real mensual
**Historia:** Como agente, necesito un solo número comparable entre rentar y comprar, con su desglose.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular costo real mensual = pago de vivienda (renta, o mensualidad de compra) + transporte + servicios + tiempo valorizado.
2. EL SISTEMA DEBERÁ devolver el desglose completo: cada componente con `monto_mxn` (entero), `fuente`, `fecha_dato` y lista de supuestos usados.
3. EL SISTEMA DEBERÁ devolver también el costo monetario (sin tiempo valorizado) y el porcentaje del ingreso mensual que representa cada uno.
4. CUANDO la operación sea compra, EL SISTEMA DEBERÁ indicar que el enganche no está incluido en el costo mensual y mostrarlo por separado.
5. SI el precio del inmueble supera `Perfil.presupuesto_max_mxn`, ENTONCES EL SISTEMA DEBERÁ marcar `excede_presupuesto = true`.
6. CUANDO falte algún dato para un componente, EL SISTEMA DEBERÁ marcar ese componente como no calculable con el motivo y NO DEBERÁ sustituirlo por un valor inventado.
7. EL SISTEMA DEBERÁ redondear todos los montos a pesos enteros (MXN), con el redondeo aplicado una sola vez al final de cada componente.

### R7. Precio justo
**Historia:** Como usuario, quiero saber si el precio del anuncio es razonable para su colonia.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular precio por m² = `precio_mxn` ÷ `m2` y compararlo con la mediana de su colonia para la misma operación.
2. EL SISTEMA DEBERÁ clasificar con la razón de precio en una de tres bandas, con umbrales en la tabla de supuestos:
   - `sospechosamente_barato`: razón < 0.70.
   - `justo`: razón entre 0.70 y 1.15, ambos incluidos.
   - `caro`: razón > 1.15.
3. EL SISTEMA DEBERÁ devolver la razón, el precio por m², la mediana, la diferencia porcentual y el número de anuncios en que se basa la mediana, si está disponible.
4. SI el inmueble no tiene `m2` o la colonia no tiene mediana para esa operación, ENTONCES EL SISTEMA DEBERÁ devolver `no_evaluable` con el motivo y NO DEBERÁ inventar una referencia.
5. CUANDO la banda sea `sospechosamente_barato`, EL SISTEMA DEBERÁ explicar que puede ser una oportunidad o una señal de fraude, y remitir a la evaluación antifraude de la spec 04 sin emitir juicio por sí misma.
6. EL SISTEMA DEBERÁ citar la fuente y la fecha de la mediana (por ejemplo "Mediana de anuncios capturados, Roma Norte, 2026-11-14") y avisar cuando la mediana provenga de anuncios sintéticos.
7. EL SISTEMA DEBERÁ usar los mismos valores de mediana que la spec 04, sin recalcularlos.

### R8. Trazabilidad, supuestos y determinismo
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ concentrar todos los supuestos numéricos en `data/raw/calculos_supuestos.json` y `data/raw/tarifas_semovi.json`, cada uno con `fuente`, `fecha_dato` y descripción.
2. EL SISTEMA DEBERÁ registrar los supuestos y tarifas en `data/raw/FUENTES.md`.
3. LAS funciones de cálculo DEBERÁN ser puras: sin red, sin lectura de archivos y sin reloj; reciben `Inmueble`, `Perfil`, `Colonia` y la configuración como parámetros.
4. EL SISTEMA DEBERÁ marcar `es_sintetico = true` cuando el inmueble tenga `fuente = "sintetico"` y el agente deberá decirlo.
5. LOS textos de explicación DEBERÁN usar lenguaje simple, con acentos y sin jerga inmobiliaria o financiera sin definir.
6. EL SISTEMA NO DEBERÁ llamar a ningún LLM.

### R9. Pruebas
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ tener pruebas unitarias con valores calculados a mano para: haversine, tiempo por modo, pasajes, costo de auto, tiempo valorizado, servicios, mensualidad (incluye enganche ≥ precio y tasa 0) y cada banda de precio justo (incluidos los límites 0.70 y 1.15).
2. EL SISTEMA DEBERÁ tener pruebas de los casos sin dato (`no_evaluable`, sin ubicación, sin mediana).
3. EL SISTEMA DEBERÁ tener una prueba de determinismo (misma entrada, mismo resultado) y una de que el cálculo no accede a la red.
4. LAS pruebas de Nominatim y Banxico DEBERÁN usar simulaciones (mocks); ninguna prueba requiere red ni tokens.
5. EL SISTEMA DEBERÁ tener una prueba que calcule el costo real de todos los inmuebles de `data/processed/inmuebles.json` con un perfil de ejemplo, sin errores.
