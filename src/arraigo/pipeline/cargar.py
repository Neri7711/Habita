"""Carga y validación de anuncios; medianas por colonia (tareas 3.3 y 3.4)."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

from pydantic import ValidationError

from arraigo.pipeline.colonias import FECHA_CENTROIDE, FUENTE_CENTROIDE, centroides, normalizar
from arraigo.schemas import Colonia, Dato, Inmueble, Punto


def _limpiar(fila: dict, catalogo: dict[str, dict]) -> tuple[dict, list[str]]:
    """Celdas vacías → None, requisitos a lista, colonia al nombre canónico. Devuelve (fila, motivos)."""
    datos = {k: (v.strip() if isinstance(v, str) else v) or None for k, v in fila.items()}
    datos["requisitos"] = [r for r in (datos.get("requisitos") or "").split(";") if r]
    for campo in ("ubicacion_aproximada", "estacionamiento", "es_fraude_prueba", "descripcion"):
        if datos.get(campo) is None:
            datos.pop(campo, None)  # deja que aplique el default del esquema
    colonia = datos.get("colonia")
    if not colonia:
        return datos, ["colonia vacía"]
    entrada = catalogo.get(normalizar(colonia))
    if entrada is None:
        return datos, [f"colonia fuera del catálogo piloto: {colonia}"]
    datos["colonia"] = entrada["colonia"]
    datos.setdefault("alcaldia", entrada["alcaldia"])
    return datos, []


def validar_anuncios(raw_dir: Path, catalogo: dict[str, dict]) -> tuple[list[Inmueble], list[dict]]:
    """Lee data/raw/anuncios_*.csv. Devuelve (válidos, rechazados[{archivo, fila, motivos}])."""
    contexto = {"centroides": centroides(catalogo)}
    validos, rechazados = [], []
    for archivo in sorted(raw_dir.glob("anuncios_*.csv")):
        with archivo.open(encoding="utf-8", newline="") as f:
            for n, fila in enumerate(csv.DictReader(f), start=2):  # 2 = primera fila tras el encabezado
                datos, motivos = _limpiar(fila, catalogo)
                if not motivos:
                    try:
                        validos.append(Inmueble.model_validate(datos, context=contexto))
                        continue
                    except ValidationError as e:
                        motivos = [f"{'.'.join(map(str, err['loc'])) or 'registro'}: {err['msg']}" for err in e.errors()]
                rechazados.append({"archivo": archivo.name, "fila": n, "motivos": motivos})
    return validos, rechazados


def construir_colonias(catalogo: dict[str, dict], validos: list[Inmueble]) -> list[Colonia]:
    """Centroide + mediana de precio/m2 por operación.

    Usa los anuncios reales (captura_manual) si hay; si no, los sintéticos, marcados PROVISIONAL en `fuente`.
    shortcut: medianas de sintéticos (calibrados con una tabla estimada); cambiar en cuanto haya anuncios reales.
    """
    colonias = []
    for c in catalogo.values():
        medianas = {}
        for op in ("renta", "venta"):
            grupo = [i for i in validos if i.colonia == c["colonia"] and i.operacion.value == op and i.m2]
            reales = [i for i in grupo if i.fuente.startswith("captura_manual")]
            base, origen = (reales, "anuncios capturados a mano") if reales else (
                grupo, "anuncios sintéticos (PROVISIONAL, no es dato de mercado)")
            if base:
                medianas[op] = Dato[float](
                    valor=round(statistics.median(i.precio_mxn / i.m2 for i in base), 1),
                    fuente=f"mediana de {len(base)} {origen}",
                    fecha_dato=max(i.fecha_captura for i in base),
                )
            else:
                medianas[op] = Dato[float]()
        colonias.append(Colonia(
            nombre=c["colonia"],
            alcaldia=c["alcaldia"],
            centroide=Dato[Punto](valor=Punto(lat=c["lat"], lng=c["lng"]), fuente=FUENTE_CENTROIDE, fecha_dato=FECHA_CENTROIDE),
            precio_m2_renta_mediana=medianas["renta"],
            precio_m2_venta_mediana=medianas["venta"],
        ))
    return colonias


def escribir_salidas(out_dir: Path, validos: list[Inmueble], rechazados: list[dict], colonias: list[Colonia]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inmuebles.json").write_text(
        json.dumps([i.model_dump(mode="json") for i in validos], ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "colonias.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in colonias], ensure_ascii=False, indent=1), encoding="utf-8")
    with (out_dir / "rechazados.jsonl").open("w", encoding="utf-8") as f:
        for r in rechazados:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
