"""Evaluación contra es_fraude_prueba (solo aquí se lee esa etiqueta) y escritura de reportes."""
from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from arraigo.antifraude.modelos import RAIZ, ConfigReglas, ContextoAntifraude, ResultadoAntifraude, cargar_config
from arraigo.antifraude.score import construir_contexto, evaluar_anuncio
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble

META_RECALL = 0.85
META_PRECISION = 0.80
UMBRALES_CURVA = (20, 30, 40, 50, 60)

ADVERTENCIAS = [
    "Las etiquetas de los anuncios sintéticos se generaron con patrones parecidos a las reglas, "
    "por lo que la métrica sobre sintéticos es optimista.",
    "Hay pocos anuncios reales. Los reales (sin fraude) sirven para medir falsos positivos, no recall.",
    "`es_fraude_prueba` es una etiqueta de prueba, no verdad de campo.",
]


def cargar_inmuebles(ruta: Path) -> list[Inmueble]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return [Inmueble.model_validate(d) for d in datos]


def cargar_colonias(ruta: Path) -> list[Colonia]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return [Colonia.model_validate(d) for d in datos]


def evaluar_dataset(inmuebles: list[Inmueble], contexto: ContextoAntifraude) -> dict[str, ResultadoAntifraude]:
    return {i.id: evaluar_anuncio(i, contexto) for i in inmuebles}


def _razon(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def matriz_confusion(pares: list[tuple[bool, int]], umbral: int) -> dict:
    """pares = [(es_fraude_prueba, score)]."""
    tp = sum(1 for f, s in pares if f and s >= umbral)
    fp = sum(1 for f, s in pares if not f and s >= umbral)
    fn = sum(1 for f, s in pares if f and s < umbral)
    tn = sum(1 for f, s in pares if not f and s < umbral)
    return {
        "umbral": umbral, "n": len(pares), "fraudes": tp + fn,
        "vp": tp, "fp": fp, "fn": fn, "vn": tn,
        "precision": _razon(tp, tp + fp), "recall": _razon(tp, tp + fn),
    }


def _pares(inmuebles: list[Inmueble], res: dict[str, ResultadoAntifraude], filtro: Callable[[Inmueble], bool]):
    return [(i.es_fraude_prueba, res[i.id].score_riesgo) for i in inmuebles if filtro(i)]


def _cumple(m: dict) -> bool:
    return (m["recall"] or 0) >= META_RECALL and (m["precision"] or 0) >= META_PRECISION


def construir_reporte(
    inmuebles: list[Inmueble], resultados: dict[str, ResultadoAntifraude], config: ConfigReglas
) -> dict:
    u = config.umbral_alerta
    cortes = {
        "todos": lambda i: True,
        "reales": lambda i: i.fuente != "sintetico",
        "sinteticos": lambda i: i.fuente == "sintetico",
    }
    metricas = {nombre: matriz_confusion(_pares(inmuebles, resultados, f), u) for nombre, f in cortes.items()}

    en_fraude: Counter[str] = Counter()
    en_no_fraude: Counter[str] = Counter()
    for i in inmuebles:
        destino = en_fraude if i.es_fraude_prueba else en_no_fraude
        for s in resultados[i.id].senales:
            destino[s.regla] += 1
    reglas = {
        r: {"en_fraudes": en_fraude[r], "en_no_fraudes": en_no_fraude[r], "peso": config.peso(r)}
        for r in config.reglas
    }

    def detalle(i: Inmueble) -> dict:
        r = resultados[i.id]
        return {
            "id": i.id, "score": r.score_riesgo, "operacion": i.operacion.value, "colonia": i.colonia,
            "senales": [s.regla for s in r.senales], "no_evaluables": r.no_evaluables,
        }

    fn = [detalle(i) for i in inmuebles if i.es_fraude_prueba and resultados[i.id].score_riesgo < u]
    fp = [detalle(i) for i in inmuebles if not i.es_fraude_prueba and resultados[i.id].score_riesgo >= u]
    curva = [matriz_confusion(_pares(inmuebles, resultados, cortes["todos"]), t) for t in UMBRALES_CURVA]
    todos = metricas["todos"]
    return {
        "version_reglas": config.version,
        "umbral_alerta": u,
        "metas": {"recall_min": META_RECALL, "precision_min": META_PRECISION, "cumple": _cumple(todos)},
        "metricas": metricas,
        "contribucion_reglas": reglas,
        "curva_umbral": curva,
        "falsos_negativos": fn,
        "falsos_positivos": fp,
        "advertencias": ADVERTENCIAS,
        "interfaz": {
            "funcion": "arraigo.antifraude.evaluar_anuncio(inmueble, contexto) -> ResultadoAntifraude",
            "contexto": "arraigo.antifraude.construir_contexto(inmuebles, colonias)",
            "anuncio_nuevo": "arraigo.antifraude.evaluar_anuncio_nuevo(descripcion, precio_mxn, colonia, contexto)",
            "resultado_precalculado": "data/processed/antifraude.json (por id)",
        },
    }


def _fmt(x: float | None) -> str:
    return "n/d" if x is None else f"{x:.2f}"


def reporte_a_markdown(rep: dict) -> str:
    m = rep["metas"]
    L = ["# Reporte antifraude", ""]
    L.append(f"Umbral de alerta: **{rep['umbral_alerta']}** · versión de reglas: {rep['version_reglas']}")
    L.append("")
    if m["cumple"]:
        L.append(f"Meta de la demo (recall ≥ {m['recall_min']}, precisión ≥ {m['precision_min']}): **se cumple**.")
    else:
        L.append(f"Meta de la demo (recall ≥ {m['recall_min']}, precisión ≥ {m['precision_min']}): **NO se cumple**.")
    L += ["", "## Advertencias"] + [f"- {a}" for a in rep["advertencias"]]
    L += ["", "## Métricas", "", "| Corte | Anuncios | Fraudes | VP | FP | FN | VN | Precisión | Recall |", "|---|---|---|---|---|---|---|---|---|"]
    for nombre, x in rep["metricas"].items():
        L.append(
            f"| {nombre} | {x['n']} | {x['fraudes']} | {x['vp']} | {x['fp']} | {x['fn']} | {x['vn']} "
            f"| {_fmt(x['precision'])} | {_fmt(x['recall'])} |"
        )
    L += ["", "## Contribución por regla", "", "| Regla | Peso | En fraudes | En no fraudes |", "|---|---|---|---|"]
    for r, x in rep["contribucion_reglas"].items():
        L.append(f"| {r} | {x['peso']} | {x['en_fraudes']} | {x['en_no_fraudes']} |")
    L += ["", "## Curva de umbral (todos)", "", "| Umbral | Precisión | Recall | FP | FN |", "|---|---|---|---|---|"]
    for x in rep["curva_umbral"]:
        L.append(f"| {x['umbral']} | {_fmt(x['precision'])} | {_fmt(x['recall'])} | {x['fp']} | {x['fn']} |")
    for titulo, clave in (("Falsos negativos", "falsos_negativos"), ("Falsos positivos", "falsos_positivos")):
        L += ["", f"## {titulo}"]
        if not rep[clave]:
            L.append("- (ninguno)")
        for d in rep[clave]:
            L.append(f"- {d['id']} (score {d['score']}, {d['colonia']}): señales = {', '.join(d['senales']) or 'ninguna'}")
    L += ["", "## Interfaz para la spec 05 (`score_fraude`)"]
    L += [f"- {k}: `{v}`" for k, v in rep["interfaz"].items()]
    return "\n".join(L) + "\n"


def ejecutar(
    ruta_inmuebles: Path | None = None,
    ruta_colonias: Path | None = None,
    carpeta_salida: Path | None = None,
    config: ConfigReglas | None = None,
) -> dict:
    """Evalúa todo el dataset y escribe antifraude.json y reporte_antifraude.json/.md. Devuelve el reporte."""
    procesado = RAIZ / "data" / "processed"
    inmuebles = cargar_inmuebles(ruta_inmuebles or procesado / "inmuebles.json")
    colonias = cargar_colonias(ruta_colonias or procesado / "colonias.json")
    config = config or cargar_config()
    contexto = construir_contexto(inmuebles, colonias, config)
    resultados = evaluar_dataset(inmuebles, contexto)
    reporte = construir_reporte(inmuebles, resultados, config)

    salida = carpeta_salida or procesado
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "antifraude.json").write_text(
        json.dumps({k: v.model_dump(mode="json") for k, v in resultados.items()}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    (salida / "reporte_antifraude.json").write_text(
        json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (salida / "reporte_antifraude.md").write_text(reporte_a_markdown(reporte), encoding="utf-8")
    return reporte
