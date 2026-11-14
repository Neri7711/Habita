# Spec 01: Modelo de datos y dataset base

## Introducción
Definir los esquemas de datos del sistema y cargar el dataset inicial (anuncios + datos de colonia)
que usarán todas las fases posteriores. Esta spec **no incluye LLM ni interfaz**.

## Requerimientos

### R1. Esquema de inmueble
**Historia:** Como sistema, necesito una estructura única para cualquier anuncio, de renta o de venta.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ representar cada inmueble con: id, operacion (renta|venta), precio_mxn, colonia, alcaldia,
   lat, lng, m2, recamaras, banos, estacionamiento, acepta_mascotas, amueblado, requisitos (aval|poliza|deposito_extra|ninguno),
   descripcion, fuente, fecha_captura, url_origen (opcional).
2. CUANDO un registro no tenga lat/lng, EL SISTEMA DEBERÁ marcarlo como `ubicacion_aproximada = true` y usar el centroide de la colonia.
3. SI un registro tiene precio <= 0 o falta colonia, ENTONCES EL SISTEMA DEBERÁ rechazarlo y registrar el motivo en un log de validación.

### R2. Esquema de perfil de usuario
**Historia:** Como agente, necesito un perfil estructurado para filtrar y rankear.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ representar el perfil con: operacion_deseada (renta|compra|ambas), presupuesto_max_mxn,
   ingreso_mensual_mxn, destino_trabajo (lat, lng, direccion), modo_transporte (transporte_publico|auto|bici|mixto),
   tiempo_max_traslado_min, recamaras_min, mascotas, tiene_aval, enganche_disponible_mxn (si compra),
   prioridades (lista ordenada: precio, traslado, seguridad, comunidad, espacio).
2. EL SISTEMA DEBERÁ validar el perfil con un esquema (por ejemplo, Pydantic o Zod) y rechazar campos fuera de rango.

### R3. Esquema de colonia
**Historia:** Como sistema, necesito datos de contexto por colonia para calcular el costo real y el encaje con la comunidad.
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ guardar por colonia: nombre, alcaldia, centroide, precio_m2_renta_mediana, precio_m2_venta_mediana,
   indice_delitos (normalizado 0-1), estaciones_transporte_cercanas, nivel_riesgo (sísmico/inundación),
   indicador_presion_gentrificacion (0-1), puntos_comunidad (mercados, parques, centros culturales).
2. Cada campo DEBERÁ incluir `fuente` y `fecha_dato`.

### R4. Carga del dataset
**Criterios de aceptación:**
1. EL SISTEMA DEBERÁ cargar los anuncios desde un CSV/JSON en `data/raw/` hacia `data/processed/`.
2. EL SISTEMA DEBERÁ incluir entre 200 y 500 anuncios de 10 a 15 colonias piloto, con renta y venta.
3. EL dataset DEBERÁ incluir al menos 15 anuncios marcados como `es_fraude_prueba = true` para evaluar la fase de antifraude.
4. EL SISTEMA DEBERÁ generar un reporte de calidad: registros válidos, rechazados, y campos faltantes por columna.

### R5. Pruebas
1. EL SISTEMA DEBERÁ tener pruebas unitarias para la validación de cada esquema.
2. EL SISTEMA DEBERÁ tener una prueba que cargue el dataset completo sin errores.
