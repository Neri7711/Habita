# Producto: Arraigo (nombre provisional)

## Problema
Las personas que se mudan a la Ciudad de México por trabajo eligen dónde vivir con información incompleta:
no saben si un precio es justo, cuánto les costará realmente vivir en una zona (traslados, tiempo, servicios),
si un anuncio es confiable, ni cómo integrarse a la colonia. Al mismo tiempo, las reubicaciones laborales
presionan los precios en colonias populares y contribuyen al desplazamiento de residentes de toda la vida.

## Propuesta de valor
Un agente asesor que **solo recomienda** (no publica inmuebles, no contacta caseros, no cobra comisiones).
A partir del perfil del usuario, propone las mejores opciones para **rentar o comprar** y explica:
1. **Costo real de vivir**: renta o mensualidad + transporte + tiempo de traslado valorizado + servicios.
2. **Precio justo**: comparación contra la referencia de la colonia.
3. **Confiabilidad del anuncio**: señales de fraude explicadas en lenguaje simple.
4. **Encaje con la comunidad**: qué ofrece la colonia (comercio local, espacios públicos, transporte) y cómo integrarse.
5. **Reubicación consciente**: señala cuando una zona está bajo fuerte presión de gentrificación y sugiere alternativas equilibradas.

## Usuario principal
Personas con ingreso estable (empleados formales, 25-45 años, solteros, parejas o familias pequeñas)
que se reubican a CDMX por motivo laboral, desde otro estado o país, o dentro de la misma zona metropolitana.

## Alcance del MVP (competencia)
- Ciudad: CDMX, con 10 a 15 colonias piloto.
- Operaciones: renta y compra (la compra incluye una estimación de mensualidad con crédito, no una asesoría hipotecaria).
- El agente recomienda y explica. No ejecuta acciones a nombre del usuario.
- Datos: fuentes abiertas oficiales + un dataset de anuncios recolectado y documentado por el equipo.

## Fuera de alcance
- Marketplace propio, pagos, contratos, contacto automático con caseros.
- Scraping automatizado de portales.
- Asesoría legal o financiera vinculante.

## Criterios de éxito (alineados al jurado: impacto social y comunidad)
- El usuario entiende **por qué** se le recomienda cada opción (todas las recomendaciones tienen una explicación).
- Cada recomendación muestra costo real, precio justo y nivel de confianza.
- Cada recomendación incluye al menos un dato de comunidad de la colonia.
- Detectar los anuncios sospechosos del dataset de prueba.

## Principios del agente
- El LLM conversa, decide qué herramienta usar y explica. Los cálculos y filtros se hacen en código determinista.
- Siempre cita la fuente del dato (por ejemplo, "Datos Abiertos CDMX, 2025").
- Nunca inventa precios ni inmuebles. Si no hay datos, lo dice.
- Tono: claro, cercano, sin jerga inmobiliaria.
