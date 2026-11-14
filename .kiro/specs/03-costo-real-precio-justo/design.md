# Diseño — Spec 03: Costo real y precio justo

## Decisiones clave
| Tema | Decisión | Por qué |
|---|---|---|
| Traslado | Haversine × factor de rodeo ÷ velocidad por modo | Sin API de rutas ni cuentas; reproducible y explicable (tech.md) |
| Destino | Geocodificar con `arraigo.fuentes.nominatim` solo en `pipeline/referencias.py` | Las funciones de `calculos/` quedan puras y sin red |
| Tarifas | Tabla fija `data/raw/tarifas_semovi.json` con URL y fecha por tarifa | Cambian pocas veces al año; no hay API oficial estable |
| Pasajes | Número de pasajes por tramos de distancia de ruta | Aproxima transbordos sin conocer la red de transporte |
| Tiempo | Ingreso/hora × horas de traslado al mes × `factor_valor_tiempo` (1.0) | Fórmula pedida; el factor permite sensibilidad sin tocar código |
| Servicios | Base + monto por recámara, marcado como supuesto | No hay fuente abierta por inmueble; se declara como supuesto |
| Hipoteca | Cuota fija (amortización francesa) con tasa = TIIE 28 días (Banxico) + spread | Fuente oficial gratuita; el spread es supuesto explícito |
| Precio justo | Razón precio/m² ÷ mediana de la colonia, tres bandas | Una sola referencia, la misma de la spec 04 |
| Redondeo | Pesos enteros, una sola vez al final de cada componente | Evita errores acumulados; montos `int` (tech.md) |
| Resultado | Cada componente es un `Dato[int]` con `fuente` y `fecha_dato` | Reutiliza el contrato de procedencia de la spec 01 |
| Texto | Las plantillas de explicación viven en `calculos/`; el LLM solo las parafrasea | Evita que el LLM invente cifras |

## Módulos
```
src/arraigo/calculos/
├── __init__.py
├── supuestos.py     # ConfigCalculos, TarifasSemovi, cargar_config(), cargar_tarifas()
├── traslado.py      # haversine_km(), estimar_traslado()
├── transporte.py    # costo_transporte_mensual()
├── tiempo.py        # tiempo_valorizado()
├── servicios.py     # costo_servicios()
├── hipoteca.py      # mensualidad_compra()
├── precio_justo.py  # evaluar_precio_justo()
├── costo_real.py    # calcular_costo_real() (compone todo)
└── modelos.py       # resultados Pydantic
src/arraigo/pipeline/referencias.py   # I/O: geocodificar_destino(), obtener_tasa_referencia()
scripts/calcular_costos.py            # CLI: perfil JSON -> data/processed/costos.json
data/raw/calculos_supuestos.json
data/raw/tarifas_semovi.json
data/raw/tasa_referencia.json         # generado por obtener_tasa_referencia()
tests/test_calculos_*.py
```
Las funciones de `calculos/` son puras. La red y los archivos solo se tocan en `pipeline/referencias.py` y en los scripts
(regla de structure.md y tech.md). `pipeline/referencias.py` es un archivo nuevo y no choca con `pipeline/enriquecer/` de la spec 02.

## Entradas
Se usan los modelos reales de `arraigo.schemas`:
- `Inmueble`: `operacion`, `precio_mxn`, `m2`, `recamaras`, `lat`, `lng`, `ubicacion_aproximada`, `fuente`, `colonia`.
- `Perfil`: `ingreso_mensual_mxn`, `destino_trabajo` (`Ubicacion`: `lat`, `lng`, `direccion`), `modo_transporte`,
  `tiempo_max_traslado_min`, `enganche_disponible_mxn`, `presupuesto_max_mxn`.
- `Colonia`: `precio_m2_renta_mediana`, `precio_m2_venta_mediana` (`Dato[float]`) y, si la spec 02 ya corrió, `estaciones_transporte_cercanas`.

Nota: `Perfil.operacion_deseada` usa `compra`, mientras `Inmueble.operacion` usa `venta`. El cálculo se guía por `Inmueble.operacion`;
`compra`/`venta` se tratan como la misma operación.

## Supuestos (`data/raw/calculos_supuestos.json`)
Cada entrada lleva `valor`, `unidad`, `fuente` y `fecha_dato`. Los valores son **iniciales y deben revisarse** (tarea 1.2).
```json
{
  "version": 1,
  "traslado": {
    "factor_rodeo":  {"transporte_publico": 1.4, "auto": 1.3, "bici": 1.25},
    "velocidad_kmh": {"transporte_publico": 17,  "auto": 22,  "bici": 14},
    "fuente": "Supuesto del equipo: velocidades puerta a puerta en hora pico en CDMX, a validar",
    "fecha_dato": "2026-11-14"
  },
  "calendario": {"dias_laborales_mes": 22, "horas_laborales_dia": 8, "viajes_por_dia": 2},
  "pasajes_por_distancia_ruta_km": [
    {"hasta_km": 10, "pasajes": 1},
    {"hasta_km": 20, "pasajes": 2},
    {"hasta_km": null, "pasajes": 3}
  ],
  "tarifa_por_defecto_transporte_publico": "metro",
  "auto": {"costo_por_km_mxn": 3.0, "nota": "combustible (~$2.0/km) + mantenimiento (~$1.0/km); no incluye estacionamiento, seguro ni tenencia"},
  "tiempo": {"factor_valor_tiempo": 1.0},
  "servicios": {"base_mxn": 900, "por_recamara_mxn": 250,
                "desglose_pct": {"luz": 0.30, "agua": 0.15, "gas": 0.25, "internet": 0.30}},
  "compra": {"mantenimiento_predial_anual_pct": 0.006, "plazo_anios": 20, "enganche_minimo_pct": 0.10,
             "spread_sobre_tiie_pp": 3.5, "tasa_respaldo_anual_pct": 11.5,
             "serie_banxico": "SF43783", "pago_max_pct_ingreso": 0.35},
  "precio_justo": {"umbral_sospechosamente_barato": 0.70, "umbral_caro": 1.15}
}
```
El umbral 0.70 coincide con el límite superior de `precio_algo_bajo` de la spec 04. Si uno cambia, hay que revisar el otro.

## Tarifas SEMOVI (`data/raw/tarifas_semovi.json`)
```json
{
  "version": 1,
  "tarifas": {
    "metro":        {"mxn": 5,   "tipo_cobro": "viaje", "url": "<Gaceta Oficial CDMX / SEMOVI>", "fecha_vigencia": "<AAAA-MM-DD>"},
    "metrobus":     {"mxn": 6,   "tipo_cobro": "viaje", "url": "...", "fecha_vigencia": "..."},
    "trolebus":     {"mxn": 4,   "tipo_cobro": "viaje", "url": "...", "fecha_vigencia": "..."},
    "tren_ligero":  {"mxn": 3,   "tipo_cobro": "viaje", "url": "...", "fecha_vigencia": "..."},
    "rtp":          {"mxn": 2,   "tipo_cobro": "viaje", "url": "...", "fecha_vigencia": "..."},
    "cablebus":     {"mxn": 7,   "tipo_cobro": "viaje", "url": "...", "fecha_vigencia": "..."},
    "ecobici_anual":{"mxn": 521, "tipo_cobro": "anual", "url": "...", "fecha_vigencia": "..."}
  }
}
```
Los montos de arriba son de referencia y **están por verificar** contra la fuente oficial vigente (tarea 1.2). Ninguna tarifa puede quedar sin URL ni fecha (R2.8).
El tipo de estación de la spec 02 (`metro`, `metrobus`, `ecobici`, ...) se mapea a estas claves; si no hay mapeo, se usa la tarifa por defecto.

## Modelos de resultado (`calculos/modelos.py`)
```python
class Traslado(BaseModel):
    distancia_recta_km: float
    distancia_ruta_km: float
    minutos_ida: int
    modo_usado: str                  # modo de cálculo realmente aplicado ("transporte_publico" si el perfil dijo "mixto")
    excede_tiempo_max: bool
    avisos: list[str]

class Componente(BaseModel):
    monto_mxn: int | None            # None = no calculable
    fuente: str
    fecha_dato: date
    supuestos: list[str]             # frases simples: "22 días laborales al mes", "2 viajes al día"
    motivo_no_calculable: str | None = None

class Hipoteca(BaseModel):
    mensualidad_mxn: int
    enganche_mxn: int
    monto_financiado_mxn: int
    tasa_anual_pct: float            # TIIE + spread
    tasa_referencia_pct: float       # TIIE sola
    plazo_anios: int
    fuente_tasa: str                 # "Banco de México, SIE, serie SF43783" o "respaldo"
    fecha_tasa: date
    avisos: list[str]

class PrecioJusto(BaseModel):
    banda: Literal["sospechosamente_barato", "justo", "caro", "no_evaluable"]
    precio_m2: float | None
    mediana_m2: float | None
    razon: float | None
    diferencia_pct: float | None     # (razon - 1) * 100
    n_anuncios_mediana: int | None
    fuente_referencia: str | None
    es_sintetico: bool
    explicacion: str
    motivo_no_evaluable: str | None = None

class CostoReal(BaseModel):
    inmueble_id: str
    operacion: Literal["renta", "venta"]
    vivienda: Componente             # renta o mensualidad
    transporte: Componente
    servicios: Componente
    tiempo_valorizado: Componente
    horas_traslado_mes: float
    costo_monetario_mxn: int | None  # vivienda + transporte + servicios
    costo_real_mxn: int | None       # monetario + tiempo valorizado
    pct_ingreso_monetario: float | None
    pct_ingreso_real: float | None
    traslado: Traslado | None
    hipoteca: Hipoteca | None
    enganche_inicial_mxn: int | None # solo compra, no está en el costo mensual
    excede_presupuesto: bool
    pago_excede_ingreso: bool
    precio_justo: PrecioJusto
    es_sintetico: bool
    avisos: list[str]
    resumen: str                     # lenguaje simple, listo para que el agente lo cite
```

## Fórmulas
Notación: `d` = distancia haversine (km), `f` = factor de rodeo, `v` = velocidad (km/h), `D = d × f`, `N` = días laborales al mes (22).

1. **Haversine** (radio terrestre 6371.0088 km):
   `a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlng/2)`; `d = 2R·asin(√a)`.
2. **Traslado**: `D = d × f(modo)`; `minutos_ida = round(D / v(modo) × 60)`.
   `mixto` usa `transporte_publico` y agrega el aviso.
3. **Transporte público**: `pasajes = tabla(D)`; `mensual = pasajes × tarifa × 2 × N`.
   Tarifa: tipo de la estación más cercana de la colonia si existe; si no, `tarifa_por_defecto_transporte_publico`.
4. **Auto**: `mensual = D × 2 × N × costo_por_km`.
5. **Bici**: `mensual = ecobici_anual / 12`.
6. **Tiempo valorizado**:
   `ingreso_hora = ingreso_mensual / (N × 8)`;
   `horas_mes = minutos_ida × 2 × N / 60`;
   `valor = ingreso_hora × horas_mes × factor_valor_tiempo`.
7. **Servicios**: `total = base + por_recamara × recamaras`; desglose con `desglose_pct`.
   En venta se suma `precio × mantenimiento_predial_anual_pct / 12`.
8. **Mensualidad**: `i = tasa_anual/12/100`, `n = plazo_anios × 12`, `P = max(precio − enganche, 0)`;
   `cuota = P·i / (1 − (1+i)^−n)`; si `i = 0`, `cuota = P / n`; si `P = 0`, `cuota = 0`.
   `tasa_anual = TIIE28 + spread_sobre_tiie_pp`.
9. **Costo real**: `monetario = vivienda + transporte + servicios`; `real = monetario + tiempo_valorizado`.
10. **Precio justo**: `razon = (precio / m2) / mediana`;
    `razon < 0.70 → sospechosamente_barato`; `0.70 ≤ razon ≤ 1.15 → justo`; `razon > 1.15 → caro`.
    Para renta y venta se usa la mediana de su operación. Los límites se comparan sobre la razón sin redondear.

### Ejemplo hecho a mano (para las pruebas)
Renta de $18,000, 60 m², 2 recámaras; trabajo a 6.0 km en línea recta; modo transporte público; ingreso $30,000; tarifa por defecto Metro $5.
- `D = 6.0 × 1.4 = 8.4 km`; `minutos_ida = round(8.4/17×60) = round(29.65) = 30`.
- Pasajes: 8.4 km ≤ 10 → 1. Transporte: `1 × 5 × 2 × 22 = $220`.
- Ingreso/hora: `30,000 / 176 = 170.45`; horas/mes: `30 × 2 × 22 / 60 = 22`; tiempo valorizado: `$3,750`.
- Servicios: `900 + 250 × 2 = $1,400`.
- Costo monetario: `18,000 + 220 + 1,400 = $19,620`. Costo real: `19,620 + 3,750 = $23,370`.
- Si la mediana de renta de la colonia es $360/m²: `300 / 360 = 0.83` → `justo`.

Los valores de tarifa y velocidad de este ejemplo son los de la configuración inicial; las pruebas deben cargar una configuración fija de prueba, no la de `data/raw/`.

## Capa de I/O (`pipeline/referencias.py`)
- `geocodificar_destino(direccion: str) -> Ubicacion`: llama `nominatim.geocodificar`. Si regresa `None`, lanza `DireccionNoEncontrada` con mensaje en español (R1.7).
  Respeta el límite de 1 solicitud por segundo y la caché que ya implementa `fuentes/_http.py`.
- `obtener_tasa_referencia(ruta=data/raw/tasa_referencia.json) -> TasaReferencia`:
  1. Intenta `banxico.dato_oportuno("SF43783")`; convierte `dato` (texto) a `float` y `fecha` a `date`; guarda el archivo.
  2. Si falla (sin token o sin red), lee el archivo guardado.
  3. Si tampoco existe, regresa la tasa de respaldo de la configuración con `fuente_tasa = "respaldo"`.
- Ninguna de las dos se invoca desde `calculos/`; quien llama (script o servidor MCP) pasa los resultados como parámetros.

## Interfaz pública (para la spec 05)
```python
def calcular_costo_real(inmueble: Inmueble, perfil: Perfil, colonia: Colonia | None,
                        config: ConfigCalculos, tarifas: TarifasSemovi,
                        tasa: TasaReferencia | None = None) -> CostoReal: ...

def evaluar_precio_justo(inmueble: Inmueble, colonia: Colonia | None,
                         config: ConfigCalculos) -> PrecioJusto: ...
```
`costo_real` y `precio_justo` de la spec 05 llaman estas funciones. `precio_justo` no necesita perfil.

## Avisos obligatorios
- Siempre: "Estimación con supuestos; revisa los detalles antes de decidir."
- Compra: "Estimación, no es asesoría hipotecaria; no incluye comisiones, seguros ni gastos de escrituración."
- Ubicación aproximada: "Ubicación aproximada: el traslado puede variar."
- Anuncio sintético: "Este anuncio es sintético (de prueba), no un inmueble real."
- Modo `mixto`: "Para modo mixto se usó el cálculo de transporte público."
- Modo `auto`: "No incluye estacionamiento, seguro ni tenencia."
- Tasa de respaldo: "Tasa de respaldo, no es dato de Banxico."

## Errores y casos límite
| Caso | Comportamiento |
|---|---|
| Inmueble sin `lat`/`lng` | `traslado = None`; transporte y tiempo valorizado quedan `no calculable` con motivo "sin ubicación"; vivienda y servicios sí se calculan; `costo_real_mxn = None` |
| Sin `m2` o sin mediana | `precio_justo.banda = "no_evaluable"` con motivo; el costo real no se ve afectado |
| Dirección no encontrada | `DireccionNoEncontrada`; no se calcula nada |
| Sin token Banxico | Se usa la última tasa guardada, o la de respaldo, con aviso |
| Enganche ≥ precio | Mensualidad 0 con aviso |
| `Perfil.operacion_deseada = "renta"` y inmueble en venta | Se calcula igual con el enganche disponible; si el perfil no tiene enganche, la compra queda `no calculable` con motivo "sin enganche" |
| Tasa 0 | Cuota = P / n (sin dividir entre cero) |

## Estrategia de pruebas
- Configuración fija de prueba creada en el propio test (sin leer `data/raw/`).
- Valores calculados a mano (ejemplo de arriba) para cada fórmula; límites 0.70 y 1.15 con `pytest.approx` solo donde haya flotantes.
- Mocks de `nominatim.geocodificar` y `banxico.dato_oportuno`; ninguna prueba usa red ni token.
- Prueba de que `calculos/` no importa `urllib`, `requests` ni `arraigo.fuentes`.
- Prueba de integración: todos los inmuebles de `data/processed/inmuebles.json` con un perfil de ejemplo.
