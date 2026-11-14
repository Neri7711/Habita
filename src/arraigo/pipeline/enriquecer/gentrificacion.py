"""Indicador de presión de gentrificación (spec 02, R5; tareas 5.3-5.5).

Heurística transparente, no medición validada. Tres componentes, cada uno normalizado a 0-1 con rango percentil
contra todo el catálogo (las 13 colonias piloto, cada una como unión de sus unidades IECM, más el resto de las
~1,800 unidades del catálogo IECM 2019):

| Clave              | Cálculo crudo                                                         | Dirección              |
|--------------------|-----------------------------------------------------------------------|------------------------|
| densidad_airbnb    | anuncios Inside Airbnb en la colonia / km²                            | más densidad, más presión |
| cambio_educacion   | pct_posbasica_2020 − pct_posbasica_2010, en puntos porcentuales;     | más aumento, más presión |
|                    | pct_posbasica = P18YM_PB / P_18YMAS (población de 18+ con posbásica)  |                        |
| cambio_poblacion   | (POBTOT_2020 − POBTOT_2010) / POBTOT_2010, con signo invertido        | más pérdida, más presión |

Censo y AGEB (supuestos declarados):
- Solo hay geometría de AGEB 2020 (GeoJSON de Datos Abiertos CDMX en WGS84). Cada AGEB se asigna a la colonia que
  contiene su centroide; un AGEB que cruza dos colonias cuenta completo en una.
- Las claves de AGEB cambian entre censos. En lugar de agregar 2010 con un marco 2010 (no disponible en WGS84), se
  comparan solo los AGEB con la misma clave en 2010 y 2020 dentro de cada colonia (comparación pareada). Si esos AGEB
  pareados suman menos del `COBERTURA_MINIMA` de la población 2020 de la colonia, los dos componentes censales quedan
  faltantes en esa colonia en lugar de aproximarse.
- Los porcentajes se calculan sobre totales sumados, no promedios de porcentajes. Valores reservados del INEGI
  ("*", "N/D") cuentan como faltantes y ese AGEB no entra en la comparación.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from arraigo.fuentes import inside_airbnb
from arraigo.pipeline.colonias import CATALOGO_CSV, RAIZ, normalizar
from arraigo.pipeline.enriquecer.geo import asignar_a_colonia, centroide
from arraigo.pipeline.enriquecer.normalizar import rango_percentil
from arraigo.pipeline.enriquecer.poligonos import Unidad, cargar_unidades, mapear_colonia
from arraigo.schemas.colonia import Colonia, Dato, PresionGentrificacion

RAW = RAIZ / "data" / "raw"
RUTA_AIRBNB = RAW / f"airbnb_listings_{inside_airbnb.FECHA_CORTE}.csv"
RUTA_CENSO_2010 = RAW / "censo_ageb_2010_09.zip"
RUTA_CENSO_2020 = RAW / "censo_ageb_2020_09.zip"
RUTA_AGEB_2020 = RAW / "ageb_caracteristicas_demograficas_2020.geojson"

# Los pesos son un juicio del equipo, no estimados de datos. Si falta un componente, se divide entre la suma de
# los pesos disponibles y se anota en `componentes_faltantes`; si faltan todos, valor = null. Valor a 3 decimales.
PESOS: dict[str, float] = {"densidad_airbnb": 0.40, "cambio_educacion": 0.35, "cambio_poblacion": 0.25}
COBERTURA_MINIMA = 0.5
CAJA_CDMX = {"lat": (19.0, 19.6), "lng": (-99.4, -98.9)}
FECHA_DATO = date.fromisoformat(inside_airbnb.FECHA_CORTE)
FUENTE_AIRBNB = f"Inside Airbnb, corte {inside_airbnb.FECHA_CORTE} (CC BY 4.0)"
FUENTE_CENSO = "INEGI, Censo de Población y Vivienda 2010 y 2020 (AGEB)"
EXPLICACION = (
    "Estimación orientativa. Combina cuántos anuncios de renta corta hay por km², cuánto subió la escolaridad de sus "
    "habitantes y cuánto cambió su población entre 2010 y 2020. Son señales indirectas y no prueban desplazamiento."
)
EXPLICACION_SOLO_AIRBNB = (
    "Estimación orientativa basada solo en cuántos anuncios de renta corta hay por km² (no hubo datos del censo). "
    "Es una señal indirecta y no prueba desplazamiento."
)
CRUDO_DE = {
    "densidad_airbnb": "listings_por_km2",
    "cambio_educacion": "delta_pp_educacion_superior",
    "cambio_poblacion": "cambio_pct_poblacion",
}


# ---------------- cálculos puros ----------------


def presion(componentes: dict[str, float | None], pesos: dict[str, float] = PESOS) -> tuple[float | None, list[str]]:
    """Promedio ponderado de los componentes disponibles (pesos reescalados). Regresa (valor | None, faltantes)."""
    faltantes = [k for k in pesos if componentes.get(k) is None or pd.isna(componentes.get(k))]
    disponibles = {k: w for k, w in pesos.items() if k not in faltantes}
    if not disponibles:
        return None, faltantes
    total = sum(w * float(componentes[k]) for k, w in disponibles.items()) / sum(disponibles.values())
    return round(total, 3), faltantes


def componentes_normalizados(crudos: pd.DataFrame) -> pd.DataFrame:
    """De columnas crudas (`CRUDO_DE`) a componentes 0-1 por rango percentil. La población va con signo invertido."""
    salida = pd.DataFrame(index=crudos.index)
    salida["densidad_airbnb"] = rango_percentil(crudos["listings_por_km2"])
    salida["cambio_educacion"] = rango_percentil(crudos["delta_pp_educacion_superior"])
    salida["cambio_poblacion"] = rango_percentil(-crudos["cambio_pct_poblacion"])
    return salida


def agregar_censo(c2010: pd.DataFrame, c2020: pd.DataFrame, grupo_de_ageb: pd.Series) -> pd.DataFrame:
    """Cambios censales por grupo (colonia) con comparación pareada de AGEB.

    `c2010`/`c2020`: índice = clave AGEB, columnas `pob`, `p18`, `pb` (pueden traer NaN).
    `grupo_de_ageb`: clave AGEB -> grupo (NA si el centroide no cae en ninguna colonia).
    """
    grupo = grupo_de_ageb.dropna()
    p20 = c2020.join(grupo.rename("grupo"), how="inner")
    total_2020 = p20.groupby("grupo")["pob"].sum(min_count=1)

    pares = (
        c2010.add_suffix("_10")
        .join(c2020.add_suffix("_20"), how="inner")
        .join(grupo.rename("grupo"), how="inner")
    )
    pares = pares.dropna(subset=["pob_10", "pob_20", "p18_10", "p18_20", "pb_10", "pb_20"])
    s = pares.groupby("grupo")[["pob_10", "pob_20", "p18_10", "p18_20", "pb_10", "pb_20"]].sum()

    salida = pd.DataFrame(index=total_2020.index)
    salida["poblacion_2020"] = total_2020
    salida = salida.join(s, how="left")
    salida["cobertura"] = salida["pob_20"] / salida["poblacion_2020"]
    ok = (salida["cobertura"] >= COBERTURA_MINIMA) & (salida["pob_10"] > 0) & (salida["p18_10"] > 0) & (
        salida["p18_20"] > 0
    )
    salida["cambio_pct_poblacion"] = ((salida["pob_20"] - salida["pob_10"]) / salida["pob_10"]).where(ok)
    salida["delta_pp_educacion_superior"] = (
        100 * (salida["pb_20"] / salida["p18_20"] - salida["pb_10"] / salida["p18_10"])
    ).where(ok)
    return salida


def coincide_hipotesis(hipotesis: str | None, valor: float | None) -> bool | None:
    """alta: ≥ 0.66; media: 0.33-0.66; baja: < 0.33. None si falta alguno."""
    if valor is None or not hipotesis:
        return None
    h = hipotesis.strip().lower()
    if h == "alta":
        return valor >= 0.66
    if h == "media":
        return 0.33 <= valor < 0.66
    if h == "baja":
        return valor < 0.33
    return None


# ---------------- carga de archivos ----------------


def cargar_airbnb(ruta: Path = RUTA_AIRBNB) -> pd.DataFrame:
    """id, lat, lng sin nulos, sin duplicados por id y dentro de la caja de CDMX."""
    df = pd.read_csv(ruta, usecols=["id", "latitude", "longitude"]).rename(
        columns={"latitude": "lat", "longitude": "lng"}
    )
    df = df.dropna().drop_duplicates(subset="id")
    (la0, la1), (lo0, lo1) = CAJA_CDMX["lat"], CAJA_CDMX["lng"]
    return df[df["lat"].between(la0, la1) & df["lng"].between(lo0, lo1)].reset_index(drop=True)


def cargar_censo(ruta_zip: Path) -> pd.DataFrame:
    """Filas de total por AGEB urbana (MZA = 000) -> índice clave de 13 caracteres, columnas pob, p18, pb."""
    with zipfile.ZipFile(ruta_zip) as z:
        interno = next(n for n in z.namelist() if "conjunto_de_datos" in n and n.lower().endswith(".csv"))
        crudo = z.read(interno)
    df = pd.read_csv(io.BytesIO(crudo), dtype=str, encoding="utf-8", encoding_errors="replace")
    df.columns = [c.strip().upper() for c in df.columns]
    df = df[(df["MZA"] == "000") & (df["AGEB"] != "0000") & (df["LOC"] != "0000")]
    clave = df["ENTIDAD"].str.zfill(2) + df["MUN"].str.zfill(3) + df["LOC"].str.zfill(4) + df["AGEB"].str.zfill(4)
    salida = pd.DataFrame(
        {
            "pob": pd.to_numeric(df["POBTOT"], errors="coerce"),
            "p18": pd.to_numeric(df["P_18YMAS"], errors="coerce"),
            "pb": pd.to_numeric(df["P18YM_PB"], errors="coerce"),
        }
    )
    salida.index = clave.values
    return salida[~salida.index.duplicated()]


def cargar_centroides_ageb(ruta: Path = RUTA_AGEB_2020) -> pd.DataFrame:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    filas = []
    for f in datos["features"]:
        if f.get("geometry"):
            lat, lng = centroide(f["geometry"])
            filas.append({"clave": str(f["properties"]["ageb"]), "lat": lat, "lng": lng})
    return pd.DataFrame(filas).drop_duplicates("clave").set_index("clave")


def cargar_hipotesis(ruta: Path = CATALOGO_CSV) -> dict[str, str]:
    with ruta.open(encoding="utf-8", newline="") as f:
        return {normalizar(r["colonia"]): r.get("hipotesis_presion", "") for r in csv.DictReader(f)}


# ---------------- orquestación del campo ----------------


def _grupos(colonias: list[Colonia], unidades: list[Unidad]) -> tuple[dict[str, str], dict[str, dict]]:
    """unidad.id -> grupo. Grupo = nombre de la colonia piloto, o "iecm:<id>" para el resto del catálogo."""
    grupo_de = {u.id: f"iecm:{u.id}" for u in unidades}
    mapeo: dict[str, dict] = {}
    for c in colonias:
        if c.centroide.valor is None:
            mapeo[c.nombre] = {"unidades": [], "metodo": "sin_centroide"}
            continue
        m = mapear_colonia(unidades, c.nombre, c.alcaldia, c.centroide.valor.lat, c.centroide.valor.lng)
        mapeo[c.nombre] = {"unidades": m.unidades, "metodo": m.metodo}
        for uid in m.unidades:
            grupo_de[uid] = c.nombre
    return grupo_de, mapeo


def enriquecer_gentrificacion(
    colonias: list[Colonia],
    *,
    unidades: list[Unidad] | None = None,
    airbnb: pd.DataFrame | None = None,
    censo_2010: pd.DataFrame | None = None,
    censo_2020: pd.DataFrame | None = None,
    centroides_ageb: pd.DataFrame | None = None,
    hipotesis: dict[str, str] | None = None,
    cargar_archivos: bool = True,
) -> tuple[list[Colonia], dict[str, list[str]], list[dict]]:
    """Llena `indicador_presion_gentrificacion` y `presion_gentrificacion_detalle`.

    Regresa (colonias, {colonia: motivos}, filas de comparación contra `hipotesis_presion`).
    Si no hay archivos del censo, sigue solo con Airbnb (supuesto documentado en motivos y explicación).
    """
    motivos: dict[str, list[str]] = {c.nombre: [] for c in colonias}
    generales: list[str] = []
    if cargar_archivos:
        unidades = unidades if unidades is not None else cargar_unidades()
        if airbnb is None:
            airbnb = cargar_airbnb()
        if hipotesis is None:
            hipotesis = cargar_hipotesis()
        if censo_2010 is None and censo_2020 is None and centroides_ageb is None:
            faltan = [p.name for p in (RUTA_CENSO_2010, RUTA_CENSO_2020, RUTA_AGEB_2020) if not p.exists()]
            if faltan:
                generales.append(f"Censo no disponible ({', '.join(faltan)}): se usa solo la densidad de Airbnb")
            else:
                censo_2010, censo_2020 = cargar_censo(RUTA_CENSO_2010), cargar_censo(RUTA_CENSO_2020)
                centroides_ageb = cargar_centroides_ageb()
    unidades = unidades or []
    hipotesis = hipotesis or {}

    grupo_de, mapeo = _grupos(colonias, unidades)
    area = pd.Series({u.id: u.area_km2 for u in unidades}).groupby(grupo_de).sum()
    crudos = pd.DataFrame(index=area.index)

    # Airbnb
    if airbnb is not None and len(unidades):
        por_unidad = asignar_a_colonia(airbnb, {u.id: u.geometria for u in unidades})
        conteo = por_unidad.dropna().map(grupo_de).value_counts()
        crudos["listings"] = conteo.reindex(area.index).fillna(0)
        crudos["listings_por_km2"] = (crudos["listings"] / area).where(area > 0)
    else:
        crudos["listings_por_km2"] = float("nan")
        generales.append("Inside Airbnb no disponible")

    # Censo
    hay_censo = censo_2010 is not None and censo_2020 is not None and centroides_ageb is not None
    if hay_censo:
        unidad_de_ageb = asignar_a_colonia(centroides_ageb, {u.id: u.geometria for u in unidades})
        grupo_de_ageb = unidad_de_ageb.dropna().map(grupo_de)
        censal = agregar_censo(censo_2010, censo_2020, grupo_de_ageb)
        crudos = crudos.join(censal[["poblacion_2020", "cobertura", "cambio_pct_poblacion",
                                     "delta_pp_educacion_superior"]], how="left")
    else:
        for col in ("poblacion_2020", "cobertura", "cambio_pct_poblacion", "delta_pp_educacion_superior"):
            crudos[col] = float("nan")

    comps = componentes_normalizados(crudos)
    fuente = f"{FUENTE_AIRBNB}; {FUENTE_CENSO}" if hay_censo else FUENTE_AIRBNB

    salida, comparacion = [], []
    for c in colonias:
        m = motivos[c.nombre]
        m.extend(generales)
        info = mapeo[c.nombre]
        if c.nombre not in comps.index:
            m.append(f"indicador_presion_gentrificacion: sin polígono IECM ({info['metodo']})")
            salida.append(c)
            comparacion.append({"colonia": c.nombre, "hipotesis_presion": hipotesis.get(normalizar(c.nombre)),
                                "valor": None, "coincide": None})
            continue
        if info["metodo"] != "nombre":
            m.append(f"polígono por {info['metodo']} (unidades IECM {', '.join(info['unidades'])})")
        fila_c, fila_r = comps.loc[c.nombre], crudos.loc[c.nombre]
        componentes = {k: (None if pd.isna(fila_c[k]) else round(float(fila_c[k]), 3)) for k in PESOS}
        valor, faltantes = presion(componentes)
        crudos_dict = {
            v: (None if pd.isna(fila_r.get(v)) else round(float(fila_r[v]), 4)) for v in CRUDO_DE.values()
        }
        for extra in ("poblacion_2020", "cobertura"):
            crudos_dict[extra] = None if pd.isna(fila_r.get(extra)) else round(float(fila_r[extra]), 4)
        crudos_dict["area_km2"] = round(float(area[c.nombre]), 4)
        if hay_censo and "cambio_poblacion" in faltantes:
            m.append(
                f"componentes censales faltantes: AGEB pareados 2010-2020 cubren "
                f"{crudos_dict['cobertura'] or 0:.0%} de la población 2020 (mínimo {COBERTURA_MINIMA:.0%})"
            )
        explicacion = EXPLICACION if hay_censo else EXPLICACION_SOLO_AIRBNB
        if valor is None:
            m.append("indicador_presion_gentrificacion: faltan todos los componentes")
            nueva = c
        else:
            nueva = c.model_copy(
                update={
                    "indicador_presion_gentrificacion": Dato[float](
                        valor=valor, fuente=fuente, fecha_dato=FECHA_DATO, explicacion=explicacion
                    ),
                    "presion_gentrificacion_detalle": Dato[PresionGentrificacion](
                        valor=PresionGentrificacion(
                            valor=valor, componentes=componentes, componentes_faltantes=faltantes, crudos=crudos_dict
                        ),
                        fuente=fuente,
                        fecha_dato=FECHA_DATO,
                        explicacion=explicacion,
                    ),
                }
            )
        salida.append(nueva)
        h = hipotesis.get(normalizar(c.nombre))
        comparacion.append(
            {"colonia": c.nombre, "hipotesis_presion": h, "valor": valor, "coincide": coincide_hipotesis(h, valor),
             **componentes}
        )
    return salida, {k: v for k, v in motivos.items() if v}, comparacion
