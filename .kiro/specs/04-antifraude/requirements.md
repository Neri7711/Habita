# Spec 04: Antifraude (reglas deterministas + score explicable)

## Introducción
Detectar anuncios sospechosos con reglas deterministas y calcular para cada uno un score de riesgo de 0 a 100.
Cada señal que sume puntos debe explicarse en lenguaje simple, para que el agente se lo diga al usuario sin jerga.
El sistema se evalúa contra `es_fraude_prueba` del dataset de la spec 01 (precisión y recall).
Esta spec **no incluye LLM ni interfaz**, no llama a servicios externos y no contacta a nadie.
Depende de la spec 01 (`inmuebles.json`, `colonias.json`). La herramienta MCP `score_fraude` se expone en la spec 05.

## Requerimientos

### R1. Reglas deterministas
**Historia:** Como agente, necesito señales objetivas y repetibles para marcar un anuncio como sospechoso.

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ evaluar cada anuncio con un conjunto fijo de reglas; la misma entrada DEBERÁ producir siempre el mismo resultado.
2. EL SISTEMA DEBERÁ incluir al menos estas reglas:
   - `precio_muy_bajo`: el precio por m² es menor al 50% de la mediana de su colonia y operación.
   - `precio_algo_bajo`: el precio por m² está entre 50% y 70% de la mediana.
   - `deposito_antes_de_visitar`: la descripción pide depósito, apartado o transferencia antes de ver el inmueble.
   - `sin_direccion`: no hay calle ni referencia concreta y la ubicación es aproximada.
   - `solo_whatsapp`: la descripción indica contacto únicamente por WhatsApp, sin teléfono fijo, correo ni visita.
   - `whatsapp_extranjero`: el número de contacto tiene lada internacional distinta de +52.
   - `descripcion_duplicada`: la descripción es igual o casi igual a la de otro anuncio de otra colonia o con otro precio.
   - `urgencia_presion`: lenguaje de presión ("última oportunidad", "hoy mismo", "se va rápido").
   - `sin_fotos_ni_visita`: la descripción indica que no hay fotos o que no se puede visitar.
   - `sin_url_origen`: el anuncio de captura manual no trae `url_origen`.
3. CUANDO una regla no se pueda evaluar (por ejemplo, falta `m2` o no hay mediana de la colonia), EL SISTEMA DEBERÁ marcarla como `no_evaluable`, no sumar puntos y registrarlo en el resultado.
4. EL SISTEMA DEBERÁ mantener las reglas, sus pesos y sus umbrales en un solo archivo de configuración versionado (`data/raw/antifraude_reglas.json`), sin valores fijos dispersos en el código.
5. EL SISTEMA NO DEBERÁ hacer scraping, abrir enlaces de los anuncios ni consultar servicios externos para evaluar un anuncio.

### R2. Score 0-100 explicable
**Historia:** Como usuario, quiero saber qué tan confiable es un anuncio y por qué.

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ calcular `score_riesgo` entero de 0 a 100 como la suma de los pesos de las reglas activadas, limitada a 100. Mayor score = más riesgo.
2. EL SISTEMA DEBERÁ asignar un nivel: `bajo` (0-29), `medio` (30-59), `alto` (60-100). Los cortes DEBERÁN estar en la configuración.
3. POR CADA regla activada, EL SISTEMA DEBERÁ devolver: `regla`, `puntos`, `evidencia` (dato concreto: el precio por m², la mediana, la frase encontrada) y `explicacion` en lenguaje simple y sin jerga.
4. EL SISTEMA DEBERÁ devolver también un `resumen` de una o dos frases y una `recomendacion` de qué hacer (por ejemplo, "no pagues nada antes de ver el lugar y conocer a quien lo renta").
5. CUANDO el score sea `bajo`, EL SISTEMA DEBERÁ decir que no se encontraron señales, no que el anuncio sea seguro.
6. EL resultado DEBERÁ citar la fuente de la mediana usada y su `fecha_dato` (por ejemplo, "mediana de anuncios capturados, Roma Norte, 2025").
7. SI el anuncio tiene `fuente = "sintetico"`, ENTONCES el resultado DEBERÁ indicarlo para que el agente lo diga.
8. El score DEBERÁ ser una señal de riesgo, no una acusación. El texto NUNCA DEBERÁ afirmar que alguien es un estafador.

### R3. Contexto de precio
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ comparar contra la mediana de precio por m² de la misma colonia y la misma operación (renta o venta) tomada de `colonias.json`.
2. CUANDO la colonia no tenga mediana, EL SISTEMA DEBERÁ marcar las reglas de precio como `no_evaluable`.
3. EL SISTEMA DEBERÁ usar la misma mediana que usa el cálculo de precio justo de la spec 03, para no dar dos referencias distintas al usuario.

### R4. Evaluación contra `es_fraude_prueba`
**Historia:** Como equipo, necesitamos demostrar con números que el antifraude funciona.

**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ evaluar todos los anuncios de `inmuebles.json` y comparar `score_riesgo >= umbral_alerta` (por defecto 30) contra `es_fraude_prueba`.
2. EL SISTEMA DEBERÁ reportar: verdaderos positivos, falsos positivos, falsos negativos, verdaderos negativos, **precisión** y **recall**.
3. EL SISTEMA DEBERÁ reportar la evaluación por separado para anuncios reales y sintéticos, y la contribución de cada regla (cuántos fraudes y cuántos no fraudes activa).
4. EL SISTEMA DEBERÁ listar los falsos negativos y falsos positivos con su id y las señales que sí se activaron.
5. LA meta de la demo DEBERÁ ser recall ≥ 0.85 y precisión ≥ 0.80 sobre el dataset completo. Si no se cumple, el reporte DEBERÁ decirlo y no ocultarlo.
6. EL SISTEMA DEBERÁ declarar en el reporte que las etiquetas sintéticas se generaron con patrones parecidos a las reglas, por lo que la métrica sobre sintéticos es optimista, y que los anuncios reales (sin fraude) sirven para medir falsos positivos.
7. EL SISTEMA DEBERÁ escribir el reporte en `data/processed/reporte_antifraude.json` y `.md`.
8. EL SISTEMA NO DEBERÁ usar `es_fraude_prueba` como entrada de ninguna regla ni del score.

### R5. Integración
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ exponer la función pública `evaluar_anuncio(inmueble, contexto) -> ResultadoAntifraude`, lista para que la spec 05 la use como herramienta `score_fraude`.
2. EL SISTEMA DEBERÁ aceptar un anuncio nuevo (por ejemplo, texto pegado por el usuario con precio, colonia y descripción) y evaluarlo con las mismas reglas.
3. EL SISTEMA DEBERÁ escribir `data/processed/antifraude.json` con el resultado por `id` para que la spec 05 y el front lo consulten sin recalcular.
4. `ResultadoAntifraude` DEBERÁ ser un modelo Pydantic con `id`, `score_riesgo`, `nivel`, `senales`, `no_evaluables`, `resumen`, `recomendacion`, `fuente_referencia`.

### R6. Pruebas
1. EL SISTEMA DEBERÁ tener pruebas unitarias por regla: un caso que la activa, uno que no y uno `no_evaluable`.
2. EL SISTEMA DEBERÁ tener pruebas del score: suma, tope en 100, niveles y que cada señal activada traiga explicación no vacía.
3. EL SISTEMA DEBERÁ tener una prueba de evaluación sobre el dataset completo que verifique las metas de R4.5 y que no use `es_fraude_prueba` como entrada.
4. EL SISTEMA DEBERÁ tener una prueba que verifique que ningún texto de explicación contiene las palabras "estafador", "ladrón" ni "seguro".
