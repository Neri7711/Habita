"""Demo de respaldo en consola: corre las herramientas del agente sin MCP ni LLM.

Uso:
    uv run python scripts/demo_consola.py            # los 3 perfiles de data/raw/demo_perfiles.json
    uv run python scripts/demo_consola.py 2          # solo el perfil 2
    uv run python scripts/demo_consola.py fraude sint-0134

Sirve si el servidor MCP no está listo o Kiro falla en vivo: muestra lo mismo que el agente le pasa a Kiro.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from arraigo.agente import herramientas as h
from arraigo.agente.contexto import cargar_contexto

RAIZ = Path(__file__).resolve().parents[1]
PERFILES = RAIZ / "data" / "raw" / "demo_perfiles.json"


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def mostrar_avisos(avisos: list[str]) -> None:
    for a in dict.fromkeys(avisos):
        print(f"   ⚠ {a}")


def demo_perfil(ctx, n: int, perfil: dict) -> None:
    destino = perfil["destino_trabajo"]["direccion"]
    titulo(
        f"PERFIL {n}: {perfil['operacion_deseada']} · tope ${perfil['presupuesto_max_mxn']:,} · "
        f"trabaja en {destino} · prioridades: {', '.join(perfil['prioridades'])}"
    )
    r = h.buscar_inmuebles(ctx, perfil, limite=3)
    print(r.explicacion)
    resultados = (r.datos or {}).get("resultados", []) if isinstance(r.datos, dict) else []
    for lugar, res in enumerate(resultados, 1):
        i = res["inmueble"]
        c = res.get("costo_real") or {}
        print(
            f"\n {lugar}. {i['id']} · {i['colonia']} · ${i['precio_mxn']:,} · {i.get('m2')} m² · "
            f"{i['recamaras']} rec. · costo real ${c.get('total_mensual_mxn', 0):,}/mes · "
            f"{c.get('minutos_traslado', '?')} min"
        )
        print(f"    Por qué: {res.get('por_que', '')}")
    if resultados:
        iid = resultados[0]["inmueble"]["id"]
        print(f"\n -- Detalle del #1 ({iid}) --")
        for nombre, env in (
            ("Costo real", h.costo_real(ctx, iid, perfil)),
            ("Precio justo", h.precio_justo(ctx, iid)),
            ("Confiabilidad", h.score_fraude(ctx, iid)),
        ):
            print(f" • {nombre}: {env.explicacion}")
        colonia = resultados[0]["inmueble"]["colonia"]
        print(f" • Comunidad: {h.info_colonia(ctx, colonia).explicacion}")
    alt = h.alternativas_equilibradas(ctx, perfil)
    print(f"\n -- Reubicación consciente --\n {alt.explicacion}")
    mostrar_avisos(r.avisos)


def demo_fraude(ctx, inmueble_id: str) -> None:
    titulo(f"ANUNCIO SOSPECHOSO: {inmueble_id}")
    for nombre, env in (("Confiabilidad", h.score_fraude(ctx, inmueble_id)), ("Precio justo", h.precio_justo(ctx, inmueble_id))):
        print(f" • {nombre}: {env.explicacion}")


def main(args: list[str]) -> None:
    ctx = cargar_contexto()
    if args[:1] == ["fraude"]:
        demo_fraude(ctx, args[1] if len(args) > 1 else "sint-0134")
        return
    perfiles = json.loads(PERFILES.read_text(encoding="utf-8"))
    elegidos = [int(a) for a in args] if args else range(1, len(perfiles) + 1)
    for n in elegidos:
        demo_perfil(ctx, n, perfiles[n - 1])
    if not args:
        demo_fraude(ctx, "sint-0134")


if __name__ == "__main__":
    main(sys.argv[1:])
