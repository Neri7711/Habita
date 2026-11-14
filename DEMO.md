# Demo de Arraigo (guion de 4 minutos)

## Antes de presentar (5 min)
```bash
uv sync
uv run python scripts/cargar_dataset.py
uv run python scripts/calcular_costos.py
uv run python scripts/enriquecer_colonias.py   # cuando la spec 02 esté integrada
uv run pytest -q
```
- Kiro abierto en el repo, con el servidor MCP `arraigo` activo (panel MCP en verde). Ver `.kiro/settings/mcp.json`.
- **Plan B**, si Kiro o MCP fallan en vivo: `uv run python scripts/demo_consola.py` muestra exactamente lo mismo en la terminal.

## 0. El problema (30 s)
"Quien se muda a CDMX por trabajo elige a ciegas: no sabe si el precio es justo, cuánto le cuesta *de verdad* vivir ahí,
si el anuncio es un fraude, ni que su llegada está empujando el desplazamiento de vecinos. Arraigo es un asesor que solo
recomienda: no vende, no cobra comisión, y siempre explica por qué."

## 1. Perfil 1: renta, trabaja en Polanco (1 min)
Escribir en el chat de Kiro:
> Me mudo a CDMX por trabajo. Voy a trabajar en Polanco, gano $45,000 al mes, quiero rentar con un tope de $18,000,
> me muevo en transporte público y no quiero hacer más de 40 minutos. Me importa sobre todo el precio y el traslado.

Qué señalar:
- **Costo real**, no solo la renta: $7,400 de renta se convierten en **~$11,300/mes** al sumar transporte, servicios y el valor del tiempo de traslado.
- **Por qué quedó #1**, en una frase.
- **Precio justo**: compara contra la mediana de la colonia **y dice de dónde sale** (hoy: anuncios de ejemplo, provisional).
- Avisos honestos: "anuncio de ejemplo", "estimación con supuestos".

## 2. Detectar un fraude (45 s), el momento "wow"
> ¿Este anuncio es confiable? sint-0134

Respuesta: **4 señales de riesgo; la más grave es que piden dinero antes de que veas el lugar.** Da un consejo concreto: no pagues, visita en persona.
Dato para el jurado: **detecta 25 de 25 fraudes de prueba, con 2 falsas alarmas** (`uv run python scripts/evaluar_antifraude.py`).

## 3. Perfil 2: compra con familia (45 s)
> Quiero comprar, tengo $640,000 de enganche y hasta $3.2 millones; trabajo en Santa Fe, voy en auto,
> necesito 2 recámaras y tengo mascota. Me importa seguridad, comunidad y espacio.

Qué señalar: **mensualidad estimada con la tasa real de Banxico** (TIIE + 3.5 pts ≈ 10% anual), sin ser asesoría hipotecaria.

## 4. Comunidad y reubicación consciente (45 s), el impacto social
> ¿Qué tiene Roma Norte para alguien que llega? ¿Hay alguna alternativa con menos presión de gentrificación?

Qué señalar: datos de **comunidad** (mercados, parques, cultura y comercio local del DENUE) y la **alternativa equilibrada**:
"si te importa no empujar el desplazamiento, mira esta colonia con costo y traslado similares".

## Cierre (15 s)
"Todo cálculo es código determinista con fuente citada: Datos Abiertos CDMX, INEGI, Banxico, OpenStreetMap, Inside Airbnb.
El LLM solo conversa y explica. Nunca inventa precios ni inmuebles."

## Preguntas probables del jurado
| Pregunta | Respuesta corta |
|---|---|
| ¿Los anuncios son reales? | El dataset de la competencia es sintético y está marcado; el agente lo avisa. La carga acepta anuncios reales capturados a mano (`data/raw/anuncios_reales.csv`) y las medianas cambian solas. |
| ¿Cómo calculan el traslado? | Distancia en línea recta × factor de rodeo ÷ velocidad por modo. Es una estimación documentada, sin API de pago. |
| ¿Qué es "presión de gentrificación"? | Indicador 0-1 con densidad de Airbnb (Inside Airbnb) y cambio entre los censos 2010 y 2020 (INEGI). La fórmula está en la spec 02. |
| ¿Por qué no usan un LLM para calcular? | Para que los números sean auditables: el LLM elige la herramienta y explica, el código calcula. |
