# Diseño — Spec 01: Modelo de datos y dataset base

## Decisiones clave
| Tema | Decisión | Por qué |
|---|---|---|
| Validación | Pydantic v2 | Mismo modelo sirve luego como schema de herramientas MCP |
| Almacenamiento | Archivos JSON en `data/processed/` | Cero infraestructura |
| Origen de anuncios | **Mixto**: ~40 anuncios reales capturados a mano (3 por colonia) + generador sintético calibrado con ellos | No hay scraping ni tiempo para capturar 200+ a mano |
| Precio m2 por colonia | Mediana de los anuncios **reales** de esa colonia; si no hay, de los sintéticos con `fuente` marcada PROVISIONAL | No existe fuente abierta por colonia y no hubo tiempo de capturar reales; se declara así en `fuente` |
| Centroides | Manuales: columnas `lat`,`lng` en `colonias_piloto.csv` | Son 13 colonias; GeoJSON + shapely no vale el tiempo. Se cita como aproximado |

## Modelos (`src/arraigo/schemas/`)

### `inmueble.py`
```python
class Operacion(str, Enum): renta = "renta"; venta = "venta"
class Requisito(str, Enum): aval; poliza; deposito_extra; ninguno

class Inmueble(BaseModel):
    id: str
    operacion: Operacion
    precio_mxn: int            # > 0
    colonia: str               # no vacío; debe existir en catálogo piloto
    alcaldia: str
    lat: float | None          # 19.0 – 19.6
    lng: float | None          # -99.4 – -98.9
    ubicacion_aproximada: bool = False
    m2: float | None           # 10 – 1000
    recamaras: int             # 0 – 10
    banos: float               # 0.5 – 10 (medios baños)
    estacionamiento: int = 0   # 0 – 10
    acepta_mascotas: bool | None
    amueblado: bool | None
    requisitos: list[Requisito] = []
    descripcion: str = ""
    fuente: str                # "captura_manual:<portal>" | "sintetico"
    fecha_captura: date
    url_origen: HttpUrl | None = None
    es_fraude_prueba: bool = False
```
- Validador de modelo: si `lat` o `lng` es `None` → se completan con el centroide de la colonia y `ubicacion_aproximada=True`
  (el centroide se inyecta desde el pipeline vía `model_validate(..., context={"centroides": {...}})`).

### `perfil.py`
```python
class Perfil(BaseModel):
    operacion_deseada: Literal["renta","compra","ambas"]
    presupuesto_max_mxn: int        # 1_000 – 50_000_000
    ingreso_mensual_mxn: int        # 1_000 – 2_000_000
    destino_trabajo: Ubicacion      # lat, lng (rango CDMX/ZM), direccion
    modo_transporte: Literal["transporte_publico","auto","bici","mixto"]
    tiempo_max_traslado_min: int    # 5 – 180
    recamaras_min: int = 0          # 0 – 6
    mascotas: bool = False
    tiene_aval: bool = False
    enganche_disponible_mxn: int | None   # requerido si operacion_deseada in (compra, ambas)
    prioridades: list[Literal["precio","traslado","seguridad","comunidad","espacio"]]  # sin repetidos, 1-5
```
Rango de `destino_trabajo` más amplio (zona metropolitana): lat 18.9 – 20.0, lng -99.6 – -98.6.

### `colonia.py`
```python
class Dato[T](BaseModel):        # envoltorio para R3.2
    valor: T | None
    fuente: str | None
    fecha_dato: date | None

class Colonia(BaseModel):
    nombre: str
    alcaldia: str
    centroide: Dato[Punto]
    precio_m2_renta_mediana: Dato[float]
    precio_m2_venta_mediana: Dato[float]
    indice_delitos: Dato[float]               # 0-1   (spec 02)
    estaciones_transporte_cercanas: Dato[list[Estacion]]  # (spec 02)
    nivel_riesgo: Dato[NivelRiesgo]           # sismico, inundacion  (spec 02)
    indicador_presion_gentrificacion: Dato[float]  # 0-1 (spec 02)
    puntos_comunidad: Dato[list[PuntoComunidad]]   # (spec 02)
```

## Pipeline (`src/arraigo/pipeline/`)
```
data/raw/colonias_piloto.csv ──► colonias.py: centroides (manuales) ─────────────┐
data/raw/anuncios_reales.csv ──► generar_sinteticos.py ─► anuncios_sinteticos.csv
data/raw/anuncios_*.csv ───────► cargar.py: validar cada fila ──────────┤
                                   ├─► data/processed/inmuebles.json
                                   ├─► data/processed/colonias.json  (centroide + medianas)
                                   ├─► data/processed/rechazados.jsonl  {fila, archivo, motivos[]}
                                   └─► data/processed/reporte_calidad.json + .md
```
- Normalización de nombres de colonia: minúsculas, sin acentos, sin "col." para hacer match con el catálogo.
- Rechazo (R1.3): `precio <= 0`, colonia vacía o fuera del catálogo piloto, o cualquier `ValidationError` → `rechazados.jsonl`.
- Reporte (R4.4): total, válidos, rechazados por motivo, % faltante por columna, conteo por colonia × operación,
  conteo de `es_fraude_prueba`, conteo real vs sintético.

## Generador sintético (`scripts/generar_anuncios_sinteticos.py`)
- Semilla fija (`--seed 42`) para reproducibilidad.
- Por colonia: precio m2 ~ lognormal centrada en la mediana real; m2 según recámaras; coordenadas aleatorias en un radio de 600 m del centroide.
- Meta: ~300 anuncios, ~60% renta / 40% venta, todas las colonias con ambas operaciones.
- Inyecta ≥ 20 fraudes (`es_fraude_prueba=true`) con patrones: precio < 50% de la mediana, "deposita antes de ver",
  sin fotos/dirección, contacto solo por WhatsApp extranjero, descripción duplicada de otro anuncio.
- Todo registro sintético: `fuente="sintetico"`, `url_origen=None`.

## Pruebas (`tests/`)
- `test_schema_inmueble.py`: válido mínimo; precio 0 → error; colonia vacía → error; sin lat/lng → aproximada con centroide; lat fuera de CDMX → error.
- `test_schema_perfil.py`: válido; compra sin enganche → error; prioridades repetidas → error; tiempo 0 → error.
- `test_schema_colonia.py`: campo con valor pero sin fuente → error.
- `test_cargar_dataset.py`: carga completa sin excepción; 200 ≤ válidos ≤ 500; ≥ 15 fraudes; 10-15 colonias; ambas operaciones presentes.
