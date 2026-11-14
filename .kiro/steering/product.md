# Producto: Arraigo (nombre provisional)

## Qué es
Agente asesor que **solo recomienda** dónde rentar o comprar en CDMX a personas que se reubican por trabajo.
No publica inmuebles, no contacta caseros, no cobra comisiones.

## Qué explica cada recomendación
1. **Costo real de vivir**: renta o mensualidad + transporte + tiempo de traslado valorizado + servicios.
2. **Precio justo**: comparación contra la mediana de la colonia.
3. **Confiabilidad del anuncio**: señales de fraude explicadas en lenguaje simple.
4. **Encaje con la comunidad**: comercio local, espacios públicos, transporte, cómo integrarse.
5. **Reubicación consciente**: avisa si la zona tiene alta presión de gentrificación y sugiere alternativas equilibradas.

## Usuario
Empleados formales de 25 a 45 años (solteros, parejas, familias pequeñas) que se mudan a CDMX por trabajo.

## Alcance MVP
- CDMX, 13 colonias piloto (ver `data/raw/colonias_piloto.csv`).
- Renta y compra (compra = estimación de mensualidad, no asesoría hipotecaria).
- Datos: fuentes abiertas oficiales + dataset de anuncios recolectado a mano por el equipo.

## Fuera de alcance
Marketplace, pagos, contratos, contacto con caseros, scraping automatizado, asesoría legal o financiera vinculante.

## Principios (obligatorios)
- El LLM conversa, elige herramienta y explica. **Cálculos y filtros = código determinista.**
- Siempre citar la fuente del dato (ej. "Datos Abiertos CDMX, 2025").
- Nunca inventar precios ni inmuebles. Si no hay datos, decirlo.
- Los anuncios sintéticos se marcan como `fuente = "sintetico"` y el agente lo dice.
- Tono claro, cercano, sin jerga inmobiliaria.

## Criterios de éxito (jurado: impacto social y comunidad)
- Toda recomendación trae explicación, costo real, precio justo, nivel de confianza y al menos un dato de comunidad.
- Detectar los anuncios marcados `es_fraude_prueba = true`.

## Roadmap de specs
| # | Spec | Contenido |
|---|---|---|
| 01 | modelo-datos | Esquemas Pydantic + carga y validación del dataset (sin LLM, sin UI) |
| 02 | enriquecimiento-colonias | Delitos, transporte, riesgo, comunidad, gentrificación desde fuentes abiertas |
| 03 | costo-real-precio-justo | Traslado estimado, costo de transporte, tiempo valorizado, servicios, mensualidad, precio justo |
| 04 | antifraude | Reglas deterministas + score explicable, evaluado contra `es_fraude_prueba` |
| 05 | agente-mcp | Servidor MCP con las herramientas; Kiro es el LLM |
| — | front | Lo lleva otra parte del equipo. Las specs 01-05 no tocan el front; solo exponen datos y herramientas |
