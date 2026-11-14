"""Enriquece data/processed/colonias.json con transporte, gentrificación y comunidad (spec 02, integración).

Uso (después de cargar_dataset.py y antes de calcular_costos.py):
    uv run python scripts/enriquecer_colonias.py
    uv run python scripts/enriquecer_colonias.py --campos comunidad,gentrificacion

Cada enriquecedor corre aislado: si uno falla, los demás siguen y el motivo queda en el reporte.
Delitos y riesgo no están implementados (recorte por tiempo): quedan en null y el agente dice "sin dato".
"""

from __future__ import annotations

import argparse
import json
import shutil
import traceback
from pathlib import Path

from arraigo.pipeline.enriquecer.comunidad import enriquecer_comunidad
from arraigo.pipeline.enriquecer.gentrificacion import enriquecer_gentrificacion
from arraigo.pipeline.enriquecer.transporte import enriquecer_transporte
from arraigo.schemas.colonia import Colonia

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"
RUTA = PROCESSED / "colonias.json"
CAMPOS = ("transporte", "gentrificacion", "comunidad")


def correr(nombre: str, fn, colonias: list[Colonia], reporte: dict) -> list[Colonia]:
    print(f"-> {nombre}…", flush=True)
    try:
        resultado = fn(colonias)
        nuevas, motivos = resultado[0], resultado[1]
        reporte[nombre] = {"estado": "ok", "motivos": motivos}
        if nombre == "gentrificacion" and len(resultado) > 2:
            reporte[nombre]["comparacion_hipotesis"] = resultado[2]
        return nuevas
    except Exception as e:  # fallo aislado: se conserva lo anterior
        reporte[nombre] = {"estado": "error", "error": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]}
        print(f"   ✗ {nombre} falló: {type(e).__name__}: {e}")
        return colonias


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--campos", default=",".join(CAMPOS), help=f"subconjunto de {CAMPOS}")
    campos = [c.strip() for c in p.parse_args().campos.split(",") if c.strip()]

    if not RUTA.exists():
        raise SystemExit("Falta data/processed/colonias.json: corre antes uv run python scripts/cargar_dataset.py")
    colonias = [Colonia.model_validate(d) for d in json.loads(RUTA.read_text(encoding="utf-8"))]
    reporte: dict = {}

    pasos = {
        "transporte": enriquecer_transporte,
        "gentrificacion": enriquecer_gentrificacion,
        "comunidad": enriquecer_comunidad,
    }
    for nombre in campos:
        colonias = correr(nombre, pasos[nombre], colonias, reporte)

    shutil.copyfile(RUTA, RUTA.with_suffix(".json.bak"))
    tmp = RUTA.with_suffix(".json.tmp")
    tmp.write_text(json.dumps([c.model_dump(mode="json") for c in colonias], ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(RUTA)
    (PROCESSED / "reporte_enriquecimiento.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )

    print("\nColonia                 | estaciones | comunidad | comercio | presión gentrif.")
    for c in colonias:
        est = c.estaciones_transporte_cercanas.valor
        pts = c.puntos_comunidad.valor
        com = getattr(c, "comercio_local", None)
        gen = c.indicador_presion_gentrificacion.valor
        print(
            f"{c.nombre[:23]:<23} | {len(est) if est else '—':>10} | {len(pts) if pts else '—':>9} | "
            f"{'sí' if com is not None and com.valor is not None else '—':>8} | {gen if gen is not None else '—'}"
        )
    print(f"\nEscrito: {RUTA} (copia en .bak) y reporte_enriquecimiento.json")
    for nombre, r in reporte.items():
        print(f"  {nombre}: {r['estado']}" + (f" — {r.get('error')}" if r["estado"] != "ok" else ""))


if __name__ == "__main__":
    main()
