# Diseño — Spec 04: Antifraude

## Decisiones clave
| Tema | Decisión | Por qué |
|---|---|---|
| Método | Reglas deterministas con pesos en un JSON | Explicable, reproducible y sin entrenar nada; el LLM solo redacta |
| Score | Suma de pesos de reglas activadas, tope 100 | Cada punto se puede rastrear a una señal |
| Texto | Expresiones regulares sobre `descripcion` normalizada (minúsculas, sin acentos) | Rápido, sin librerías extra |
| Duplicados | Similitud de Jaccard sobre conjuntos de palabras (shingles de 3 palabras) | Sin dependencias; suficiente para 500 anuncios |
| Referencia de precio | Mediana de precio por m² de `colonias.json` (la misma de la spec 03) | Una sola referencia para precio justo y antifraude |
| Configuración | `data/raw/antifraude_reglas.json` | Se calibra sin tocar código |
| Tono | "Señal de riesgo", nunca "estafa" | Evitar acusar a personas sin pruebas |
| Etiqueta de prueba | `es_fraude_prueba` solo se usa en la evaluación | Evita fuga de la respuesta al score |

## Módulos (`src/arraigo/antifraude/`)
```
src/arraigo/antifraude/
├── __init__.py
├── modelos.py      # Senal, ResultadoAntifraude, ContextoAntifraude, ConfigReglas
├── texto.py        # normalizar(), buscar_frase(), extraer_telefonos()
├── reglas.py       # una función pura por regla + REGISTRO
├── score.py        # evaluar_anuncio(), nivel_de_score(), redactar_resumen()
├── duplicados.py   # indice de similitud entre descripciones
└── evaluacion.py   # metricas contra es_fraude_prueba, reporte
```
Los scripts solo llaman a estas funciones (`scripts/evaluar_antifraude.py`).

## Modelos
```python
class ContextoAntifraude(BaseModel):
    medianas_m2: dict[tuple[str, Operacion], Dato[float]]   # (colonia_normalizada, operacion) -> mediana
    indice_duplicados: IndiceDuplicados                      # descripciones de los demás anuncios
    config: ConfigReglas

class Senal(BaseModel):
    regla: str
    puntos: int            # >= 1
    evidencia: str         # "Cuesta $180/m²; lo típico en Narvarez es $390/m² (46%)."
    explicacion: str       # lenguaje simple

class ResultadoAntifraude(BaseModel):
    id: str
    score_riesgo: int      # 0-100
    nivel: Literal["bajo","medio","alto"]
    senales: list[Senal]   # ordenadas por puntos, de mayor a menor
    no_evaluables: list[str]
    resumen: str
    recomendacion: str
    fuente_referencia: str | None   # "Mediana de anuncios capturados, Roma Norte, 2025-05-10"
    es_sintetico: bool
```

## Configuración (`data/raw/antifraude_reglas.json`)
```json
{
  "version": 1,
  "umbral_alerta": 30,
  "niveles": {"medio": 30, "alto": 60},
  "reglas": {
    "precio_muy_bajo":          {"peso": 40, "ratio_max": 0.50},
    "precio_algo_bajo":         {"peso": 15, "ratio_min": 0.50, "ratio_max": 0.70},
    "deposito_antes_de_visitar":{"peso": 35},
    "sin_direccion":            {"peso": 15},
    "solo_whatsapp":            {"peso": 15},
    "whatsapp_extranjero":      {"peso": 20},
    "descripcion_duplicada":    {"peso": 30, "jaccard_min": 0.80},
    "urgencia_presion":         {"peso": 10},
    "sin_fotos_ni_visita":      {"peso": 20},
    "sin_url_origen":           {"peso": 5}
  }
}
```
Pesos iniciales; se ajustan en la tarea de calibración mirando el reporte, nunca mirando solo la métrica final.
`precio_muy_bajo` y `precio_algo_bajo` son excluyentes (solo cuenta una).

## Reglas
Todas son funciones puras `(inmueble, contexto) -> Senal | None | NoEvaluable`.

| Regla | Condición | Evidencia | Explicación (lenguaje simple) |
|---|---|---|---|
| `precio_muy_bajo` | `(precio/m2) / mediana < 0.50` | precio/m², mediana, % | "Cuesta menos de la mitad de lo normal en esta colonia. Un precio así casi nunca es real." |
| `precio_algo_bajo` | ratio entre 0.50 y 0.70 | idem | "Es bastante más barato que otros anuncios de la zona. Pregunta por qué." |
| `deposito_antes_de_visitar` | frases como "deposita", "aparta con", "transferencia para apartar", "anticipo" junto a "antes de ver/visitar" o sin mención de visita | frase encontrada | "Te piden dinero antes de que veas el lugar. No pagues nada hasta visitarlo y conocer a quien lo renta." |
| `sin_direccion` | `ubicacion_aproximada` y sin patrón de calle/número ni "esquina con" / "entre calles" | "Sin calle ni referencia" | "No dice en qué calle está. Pide la dirección exacta antes de seguir." |
| `solo_whatsapp` | frases "solo whatsapp", "únicamente por whatsapp", "no llamadas" y ningún correo ni teléfono fijo | frase | "Solo se puede hablar por mensaje. Pide una llamada o ver el lugar en persona." |
| `whatsapp_extranjero` | teléfono con prefijo `+` distinto de `+52` | número parcial (últimos 4 ocultos) | "El número es de otro país. Quien renta un lugar en CDMX normalmente tiene un número mexicano." |
| `descripcion_duplicada` | Jaccard ≥ 0.80 con la descripción de otro anuncio con distinta colonia o distinto precio (>10%) | id del otro anuncio | "El mismo texto aparece en otro anuncio de otra zona o con otro precio. Es común en anuncios copiados." |
| `urgencia_presion` | frases de presión | frase | "Te apuran para decidir rápido. Tómate tu tiempo." |
| `sin_fotos_ni_visita` | "sin fotos", "no se puede visitar", "fotos por privado", "te lo muestro después de apartar" | frase | "No hay fotos ni forma de visitarlo. Sin ver el lugar no hay manera de comprobar que existe." |
| `sin_url_origen` | `fuente` empieza con `captura_manual` y `url_origen is None` | — | "No tenemos el enlace del anuncio original, así que no se puede revisar." |

- Precio por m²: `precio_mxn / m2`. Si `m2` es `None` o no hay mediana, las reglas de precio quedan `no_evaluable`.
- Falsos positivos a vigilar: "depósito" en renta legítima ("un mes de depósito" al firmar). La regla exige que la frase indique pago **antes** de ver, no el depósito normal del contrato.
- El número de teléfono se oculta parcialmente en `evidencia` para no exponer datos de contacto.

## Score
```
score = min(100, suma(puntos de reglas activadas))
nivel = alto si score >= 60, medio si score >= 30, bajo en otro caso
```
- Combinaciones: no hay reglas de interacción en el MVP; los pesos ya hacen que dos señales fuertes (ej. 40 + 35) lleguen a `alto`.
- `resumen` por plantilla, ejemplo: "Encontramos 3 señales de riesgo. La más importante: el precio es menos de la mitad de lo normal en Narvarte."
- `bajo` con 0 señales: "No encontramos señales de riesgo en lo que podemos revisar. Eso no garantiza que el anuncio sea real."
- `recomendacion` por nivel:
  - alto: "No pagues nada ni compartas documentos. Pide ver el lugar en persona y conocer a quien lo renta."
  - medio: "Confirma la dirección y visita el lugar antes de pagar cualquier cosa."
  - bajo: "Aun así, visita el lugar y no pagues antes de firmar."
- Sintético: se agrega al resumen "Este anuncio es de ejemplo (sintético)."

## Evaluación (`evaluacion.py`)
```
inmuebles.json ─► evaluar_anuncio() por cada fila ─► antifraude.json
                                   └─► comparar (score >= umbral) vs es_fraude_prueba
                                          └─► reporte_antifraude.json + .md
```
- Matriz de confusión; `precision = TP/(TP+FP)`, `recall = TP/(TP+FN)`. Si el denominador es 0, se reporta `null`, no 0.
- Métricas en tres cortes: todos, solo reales, solo sintéticos.
- Contribución por regla: veces activada en fraudes / en no fraudes.
- Curva simple de umbral (20, 30, 40, 50, 60) para justificar el umbral elegido.
- Listas de FP y FN con id, score y señales.
- Advertencias obligatorias en el reporte: (1) métrica sintética optimista, (2) pocos anuncios reales, (3) `es_fraude_prueba` no es verdad de campo.
- Calibración: los pesos se ajustan con el reporte, pero no se agregan reglas que repitan el patrón exacto de una sola frase del generador.

## Pruebas (`tests/`)
- `test_antifraude_reglas.py`: por regla, activa / no activa / no evaluable; depósito legítimo de contrato no activa `deposito_antes_de_visitar`.
- `test_antifraude_score.py`: suma, tope 100, niveles en 29/30/59/60, explicación no vacía, ausencia de palabras prohibidas, sin señales → resumen "no garantiza".
- `test_antifraude_duplicados.py`: textos idénticos, casi idénticos y distintos.
- `test_antifraude_evaluacion.py`: matriz con datos pequeños a mano; metas de recall y precisión sobre `inmuebles.json`; cambiar `es_fraude_prueba` no cambia el score.
