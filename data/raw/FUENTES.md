# Fuentes de datos

> `hipotesis_presion` en `colonias_piloto.csv` es una **hipótesis del equipo** para elegir colonias;
> el indicador real se calcula en la spec 02 y puede contradecirla.

| Archivo | Fuente | URL | Fecha de descarga | Licencia |
|---|---|---|---|---|
| colonias_piloto.csv | Selección del equipo | — | 2026-11-14 | — |
| colonias_cdmx.geojson | Datos Abiertos CDMX — "Colonias del IECM - 2022" (dataset `colonias-del-iecm-2022`) | https://datos.cdmx.gob.mx/dataset/colonias-del-iecm-2022 | _pendiente_ | CC-BY-4.0-ESP |

## APIs conectadas (`src/arraigo/fuentes/`)

| Módulo | Fuente | Token | Estado (2026-11-14) |
|---|---|---|---|
| `datos_cdmx.py` | Datos Abiertos CDMX (CKAN `package_search`, `datastore_search`) | No | ✅ probado |
| `nominatim.py` | OpenStreetMap Nominatim (geocodificación, 1 req/s) | No | ✅ probado |
| `overpass.py` | OpenStreetMap Overpass (mercados, parques, cultura, estaciones) | No | ✅ probado (servidores públicos a veces dan 502; hay espejos) |
| `inside_airbnb.py` | Inside Airbnb CDMX, corte 2026-09-23 (CC BY 4.0) | No | URL verificada, sin descargar |
| `inegi_denue.py` | INEGI DENUE (negocios cercanos) | Sí, gratis: `INEGI_TOKEN` | ✅ probado (469 negocios en 300 m de Roma Norte) |
| `banxico.py` | Banxico SIE (tasas, UDIS) | Sí, gratis: `BANXICO_TOKEN` | ✅ probado (UDIS, serie SP68257) |

Prueba en vivo: `uv run python scripts/probar_fuentes.py`.
| anuncios_reales.csv | Captura manual del equipo (sin scraping) | por anuncio en `url_origen` | _pendiente_ | — |
