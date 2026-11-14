"""Calcula el costo real de todos los inmuebles para un perfil y escribe data/processed/costos.json.

Uso: uv run python scripts/calcular_costos.py [--perfil perfil.json] [--salida data/processed/costos.json]

Sin --perfil usa un perfil de ejemplo. Si el destino de trabajo solo trae `direccion`, se geocodifica con Nominatim.
La tasa de Banxico se consulta si hay BANXICO_TOKEN; si no, se usa la última guardada o la de respaldo.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from arraigo.antifraude.texto import normalizar
from arraigo.calculos import calcular_costo_real, cargar_config, cargar_tarifas
from arraigo.pipeline.referencias import completar_medianas, geocodificar_destino, obtener_tasa_referencia
from arraigo.schemas import Colonia, Inmueble, Perfil

RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / "data" / "processed"

PERFIL_EJEMPLO = {
    "operacion_deseada": "ambas",
    "presupuesto_max_mxn": 4_000_000,
    "ingreso_mensual_mxn": 40_000,
    "destino_trabajo": {"lat": 19.4270, "lng": -99.1677, "direccion": "Paseo de la Reforma 222, Juárez, CDMX"},
    "modo_transporte": "transporte_publico",
    "tiempo_max_traslado_min": 45,
    "enganche_disponible_mxn": 500_000,
    "prioridades": ["precio", "traslado"],
}


def _leer(ruta: Path) -> list[dict]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_perfil(ruta: Path | None) -> Perfil:
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta else dict(PERFIL_EJEMPLO)
    destino = datos.get("destino_trabajo", {})
    if "lat" not in destino or "lng" not in destino:
        datos["destino_trabajo"] = geocodificar_destino(destino.get("direccion", "")).model_dump()
    return Perfil.model_validate(datos)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perfil", type=Path, default=None, help="JSON con un Perfil (por defecto, uno de ejemplo)")
    ap.add_argument("--salida", type=Path, default=PROCESADOS / "costos.json")
    args = ap.parse_args()

    perfil = cargar_perfil(args.perfil)
    config, tarifas = cargar_config(), cargar_tarifas()
    tasa = obtener_tasa_referencia(config)
    inmuebles = [Inmueble.model_validate(d) for d in _leer(PROCESADOS / "inmuebles.json")]
    colonias = completar_medianas([Colonia.model_validate(d) for d in _leer(PROCESADOS / "colonias.json")], inmuebles)
    por_nombre = {normalizar(c.nombre): c for c in colonias}

    resultados = [
        calcular_costo_real(i, perfil, por_nombre.get(normalizar(i.colonia)), config, tarifas, tasa) for i in inmuebles
    ]
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(
        json.dumps([json.loads(r.model_dump_json()) for r in resultados], ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    bandas = Counter(r.precio_justo.banda for r in resultados)
    calculables = [r for r in resultados if r.costo_real_mxn is not None]
    print(f"Tasa: {tasa.tasa_pct}% ({tasa.fuente}, {tasa.fecha})")
    print(f"Inmuebles: {len(resultados)} | con costo real: {len(calculables)} | precio justo: {dict(bandas)}")
    for r in sorted(calculables, key=lambda r: r.costo_real_mxn)[:5]:
        print(f"  {r.inmueble_id} ({r.operacion}): monetario ${r.costo_monetario_mxn:,} | real ${r.costo_real_mxn:,}")
    print(f"Escrito: {args.salida}")


if __name__ == "__main__":
    main()
