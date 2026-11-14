"""Reporte de calidad del dataset (tarea 3.5, R4.4)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from arraigo.schemas import Inmueble


def construir_reporte(validos: list[Inmueble], rechazados: list[dict]) -> dict:
    campos = list(Inmueble.model_fields)
    total_validos = len(validos) or 1
    faltantes = {
        c: round(100 * sum(getattr(i, c) in (None, "", []) for i in validos) / total_validos, 1) for c in campos
    }
    motivos = Counter(m.split(":")[0] for r in rechazados for m in r["motivos"])
    por_colonia = Counter((i.colonia, i.operacion.value) for i in validos)
    return {
        "total": len(validos) + len(rechazados),
        "validos": len(validos),
        "rechazados": len(rechazados),
        "rechazados_por_motivo": dict(motivos.most_common()),
        "pct_faltante_por_columna": {c: p for c, p in faltantes.items() if p > 0},
        "por_colonia": {
            col: {"renta": por_colonia[(col, "renta")], "venta": por_colonia[(col, "venta")]}
            for col in sorted({c for c, _ in por_colonia})
        },
        "fraudes_prueba": sum(i.es_fraude_prueba for i in validos),
        "ubicacion_aproximada": sum(i.ubicacion_aproximada for i in validos),
        "por_origen": {
            "real": sum(i.fuente.startswith("captura_manual") for i in validos),
            "sintetico": sum(i.fuente == "sintetico" for i in validos),
        },
    }


def a_markdown(r: dict) -> str:
    lineas = [
        "# Reporte de calidad del dataset", "",
        f"- Total de registros: **{r['total']}**",
        f"- Válidos: **{r['validos']}** · Rechazados: **{r['rechazados']}**",
        f"- Fraudes de prueba: **{r['fraudes_prueba']}** · Ubicación aproximada: **{r['ubicacion_aproximada']}**",
        f"- Reales: **{r['por_origen']['real']}** · Sintéticos: **{r['por_origen']['sintetico']}**", "",
        "## Rechazados por motivo", "",
    ]
    lineas += [f"- {m}: {n}" for m, n in r["rechazados_por_motivo"].items()] or ["- (ninguno)"]
    lineas += ["", "## % faltante por columna (solo columnas con faltantes)", ""]
    lineas += [f"- {c}: {p}%" for c, p in r["pct_faltante_por_columna"].items()] or ["- (ninguna)"]
    lineas += ["", "## Anuncios por colonia", "", "| Colonia | Renta | Venta |", "|---|---|---|"]
    lineas += [f"| {c} | {v['renta']} | {v['venta']} |" for c, v in r["por_colonia"].items()]
    return "\n".join(lineas) + "\n"


def escribir_reporte(out_dir: Path, reporte: dict) -> None:
    (out_dir / "reporte_calidad.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "reporte_calidad.md").write_text(a_markdown(reporte), encoding="utf-8")
