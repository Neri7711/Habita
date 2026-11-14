# Fuentes de datos

> `hipotesis_presion` en `colonias_piloto.csv` es una **hipótesis del equipo** para elegir colonias;
> el indicador real se calcula en la spec 02 y puede contradecirla.

| Archivo | Fuente | URL | Fecha de descarga | Licencia |
|---|---|---|---|---|
| colonias_piloto.csv | Selección del equipo | — | 2026-11-14 | — |
| colonias_piloto.csv (`lat`,`lng`) | Centroides manuales aproximados del equipo (~300 m); el GeoJSON del IECM se descartó por tiempo | — | 2026-11-14 | — |
| anuncios_sinteticos.csv | Generado por `scripts/generar_anuncios_sinteticos.py --seed 42` (medianas PROVISIONALES hasta tener reales). **Las medianas de precio/m2 de `colonias.json` salen de estos sintéticos: no son dato de mercado y así se dice en el demo** | — | 2026-11-14 | — |
| tarifas_semovi.json | Tarifas oficiales de transporte público (Metro, Metrobús, etc.); cada tarifa trae su URL y fecha | ver campo `fuente` por tarifa | 2026-11-14 | — |
| calculos_supuestos.json | **Supuestos del equipo** (días laborales, costo/km de auto, servicios, plazo y sobretasa hipotecaria de +3.5 pp sobre TIIE); cada uno trae su texto en `fuente` | — | 2026-11-14 | — |
| tasa_referencia.json | Banco de México, SIE, serie SF43783 (TIIE 28 días), guardada por `scripts/calcular_costos.py` con respaldo si falla la API | API SIE | 2026-11-17 (dato) | — |
| airbnb_listings_2026-09-23.csv | Inside Airbnb, Mexico City, corte 2026-09-23 (`visualisations/listings.csv`, 30,468 anuncios), bajado con `inside_airbnb.descargar_listings` | https://data.insideairbnb.com/mexico/df/mexico-city/2026-09-23/visualisations/listings.csv | 2026-11-14 | CC BY 4.0 |
| colonias_iecm_2019.geojson | IECM, "Colonias del IECM - 2019" (Datos Abiertos CDMX, dataset `coloniascdmx`), 1,814 unidades, WGS84. Polígonos para spec 02 (las colonias piloto se arman uniendo unidades, ver `pipeline/enriquecer/poligonos.py`) | https://datos.cdmx.gob.mx/dataset/04a1900a-0c2f-41ed-94dc-3d2d5bad4065/resource/8070ee81-9111-437e-a3dd-0c3cc6dce9f4/download/8070ee81-9111-437e-a3dd-0c3cc6dce9f4.json | 2026-11-14 | Términos de libre uso de Datos Abiertos CDMX (confirmar en el portal) |
| censo_ageb_2020_09.zip | INEGI, Censo de Población y Vivienda 2020, resultados por AGEB y manzana urbana, CDMX. Variables usadas: `POBTOT`, `P_18YMAS`, `P18YM_PB` (filas de total por AGEB, `MZA = 000`) | https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip | 2026-11-14 | Términos de libre uso de la información del INEGI |
| censo_ageb_2010_09.zip | INEGI, Censo de Población y Vivienda 2010, resultados por AGEB urbana, CDMX. Mismas variables en minúsculas (`pobtot`, `p_18ymas`, `p18ym_pb`); comparables con 2020 | https://www.inegi.org.mx/contenidos/programas/ccpv/2010/datosabiertos/ageb_y_manzana/resageburb_09_2010_csv.zip | 2026-11-14 | Términos de libre uso de la información del INEGI |
| ageb_caracteristicas_demograficas_2020.geojson | Datos Abiertos CDMX, "Características demográficas AGEB (Censo 2020)", WGS84, 2,433 AGEB. Se usa **solo la geometría** (centroide de cada AGEB, clave `ageb` de 13 caracteres) como marco geoestadístico | https://datos.cdmx.gob.mx/dataset/6de99912-dad3-4f74-92f5-90bac36daa58/resource/c976b73c-c876-4b2e-a333-44450086680f/download/c976b73c-c876-4b2e-a333-44450086680f.json | 2026-11-14 | Términos de libre uso de Datos Abiertos CDMX (confirmar en el portal) |

| gtfs_semovi.zip | Datos Abiertos CDMX, "GTFS estático de la Ciudad de México" (dataset `gtfs`, recurso `32ed1b6b-41cd-49b3-b7f0-b57acb0eb819`, `metadata_modified` 2026-09-01, usada como `fecha_dato`). 10 agencias; se usan METRO, MB, TL, TROLE (y ruta `route_type = 11`), CBB. El modo sale de `stop_times` → `trips` → `routes` | https://datos.cdmx.gob.mx/dataset/75538d96-3ade-4bc5-ae7d-d85595e4522d/resource/32ed1b6b-41cd-49b3-b7f0-b57acb0eb819/download/32ed1b6b-41cd-49b3-b7f0-b57acb0eb819.zip | 2026-11-14 | Términos de libre uso de Datos Abiertos CDMX (confirmar en el portal) |
| _(consulta, caché en `.cache/http`)_ | Ecobici, feed GBFS `station_information` (677 estaciones; `fecha_dato` = `last_updated` del feed). Índice: https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json | https://gbfs.mex.lyftbikes.com/gbfs/es/station_information.json | 2026-11-14 | Licencia del feed GBFS de Ecobici (confirmar) |

> Supuesto de gentrificación (spec 02, R5): no hay marco de AGEB 2010 en WGS84, así que 2010 y 2020 se comparan
> solo en los AGEB con la misma clave en ambos censos (2,430 de 2,433). En las 13 colonias piloto esos AGEB cubren
> el 100% de la población 2020. Detalle en `src/arraigo/pipeline/enriquecer/gentrificacion.py`.

## APIs conectadas (`src/arraigo/fuentes/`)

| Módulo | Fuente | Token | Estado (2026-11-14) |
|---|---|---|---|
| `datos_cdmx.py` | Datos Abiertos CDMX (CKAN `package_search`, `datastore_search`) | No | ✅ probado |
| `nominatim.py` | OpenStreetMap Nominatim (geocodificación, 1 req/s) | No | ✅ probado |
| `overpass.py` | OpenStreetMap Overpass (mercados, parques, cultura, estaciones) | No | ✅ probado (servidores públicos a veces dan 502; hay espejos) |
| `inside_airbnb.py` | Inside Airbnb CDMX, corte 2026-09-23 (CC BY 4.0) | No | ✅ descargado (2026-11-14) |
| `inegi_denue.py` | INEGI DENUE (negocios cercanos) | Sí, gratis: `INEGI_TOKEN` | ✅ probado (469 negocios en 300 m de Roma Norte) |
| `banxico.py` | Banxico SIE (tasas, UDIS) | Sí, gratis: `BANXICO_TOKEN` | ✅ probado (UDIS, serie SP68257) |

Prueba en vivo: `uv run python scripts/probar_fuentes.py`.
| anuncios_reales.csv | Captura manual del equipo (sin scraping) | por anuncio en `url_origen` | _pendiente_ | — |
