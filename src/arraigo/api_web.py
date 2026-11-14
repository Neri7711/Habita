"""API HTTP para el front (Starlette, ya viene con `mcp`; sin dependencias nuevas).

Envuelve las mismas herramientas deterministas del agente (`arraigo.agente.herramientas`).
Rutas (todas JSON, prefijo /api):
    GET  /api/salud                 estado y origen de los datos
    GET  /api/zonas                 zonas de trabajo con coordenadas (para el <select> de destino)
    GET  /api/colonias              ColoniaResumen[] + presión de gentrificación calculada
    GET  /api/stats                 StatsLanding
    GET  /api/ejemplo               RecomendacionEjemplo (búsqueda real con un perfil fijo)
    POST /api/buscar                PerfilRapido -> ResultadoBusqueda + supuestos/avisos/fuentes
    GET  /api/inmuebles/{id}        detalle: costo real, precio justo y confiabilidad

Correr:  uv run python scripts/servir_api.py   (http://127.0.0.1:8000)
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from arraigo.agente import herramientas as h
from arraigo.agente.contexto import cargar_contexto, normalizar_colonia

RAIZ = Path(__file__).resolve().parents[2]
PROCESSED = RAIZ / "data" / "processed"
PILOTO = RAIZ / "data" / "raw" / "colonias_piloto.csv"

# Zonas de trabajo frecuentes con coordenadas aproximadas (centro de la zona). Cerradas a propósito:
# el front las muestra como opciones y el texto libre se intenta empatar contra ellas.
ZONAS = [
    {"id": "reforma", "nombre": "Paseo de la Reforma", "lat": 19.4270, "lng": -99.1677},
    {"id": "polanco", "nombre": "Polanco", "lat": 19.4330, "lng": -99.1910},
    {"id": "santa-fe", "nombre": "Santa Fe", "lat": 19.3590, "lng": -99.2600},
    {"id": "centro", "nombre": "Centro Histórico", "lat": 19.4326, "lng": -99.1332},
    {"id": "insurgentes-sur", "nombre": "Insurgentes Sur / Del Valle", "lat": 19.3870, "lng": -99.1740},
    {"id": "roma-condesa", "nombre": "Roma / Condesa", "lat": 19.4150, "lng": -99.1650},
    {"id": "coyoacan", "nombre": "Coyoacán", "lat": 19.3500, "lng": -99.1620},
    {"id": "periferico-sur", "nombre": "Periférico Sur", "lat": 19.3040, "lng": -99.1900},
    {"id": "aeropuerto", "nombre": "Aeropuerto (AICM)", "lat": 19.4361, "lng": -99.0719},
]
ZONA_DEFECTO = ZONAS[0]

# Lo que el formulario corto no pregunta y el back completa. Se regresa en `supuestos` para que se vea.
SUPUESTOS_PERFIL = {
    "ingreso_por_presupuesto": 3,  # ingreso estimado = 3 × presupuesto de renta (regla 30%)
    "modo_transporte": "transporte_publico",
    "tiempo_max_traslado_min": 45,
    "prioridades": ["precio", "traslado", "comunidad"],
    "enganche_pct": 0.20,
}

CHIP_PRECIO = {"justo": ("Precio justo", "confianza"), "caro": ("Arriba de la mediana", "alerta"),
               "sospechosamente_barato": ("Sospechosamente barato", "alerta"), "sin_dato": ("Precio sin referencia", "neutro")}
CHIP_RIESGO = {"bajo": ("Riesgo bajo", "confianza"), "medio": ("Riesgo medio", "alerta"), "alto": ("Riesgo alto", "alerta")}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return " ".join(t.replace("/", " ").split())


def _asegurar_datos() -> None:
    """Si data/processed está vacío, corre la carga y el costo (offline salvo Banxico, que tiene respaldo)."""
    if (PROCESSED / "inmuebles.json").exists() and (PROCESSED / "colonias.json").exists():
        return
    for script in ("cargar_dataset.py", "calcular_costos.py"):
        subprocess.run([sys.executable, str(RAIZ / "scripts" / script)], cwd=RAIZ, check=True)


@lru_cache(maxsize=1)
def contexto():
    _asegurar_datos()
    return cargar_contexto()


def resolver_zona(texto: str) -> tuple[dict, str | None]:
    """Zona por id o por nombre parecido; si no, Nominatim; si no, la zona por defecto con aviso."""
    n = _norm(texto)
    for z in ZONAS:
        if n and (n == z["id"] or n in _norm(z["nombre"]) or _norm(z["nombre"]).split(" ")[0] in n):
            return z, None
    try:
        from arraigo.fuentes import nominatim

        g = nominatim.geocodificar(f"{texto}, Ciudad de México")
        if g and 19.0 <= g["lat"] <= 19.7 and -99.4 <= g["lng"] <= -98.9:
            return {"id": "geocodificado", "nombre": texto, "lat": g["lat"], "lng": g["lng"]}, (
                f"Ubicamos «{texto}» con OpenStreetMap (aproximado).")
    except Exception:
        pass
    return ZONA_DEFECTO, f"No reconocimos «{texto}»; usamos {ZONA_DEFECTO['nombre']} como destino aproximado."


def perfil_completo(rapido: dict) -> tuple[dict, list[str]]:
    operacion = "compra" if rapido.get("operacion") == "compra" else "renta"
    presupuesto = int(rapido.get("presupuesto_max_mxn") or 0)
    if not 1_000 <= presupuesto <= 50_000_000:
        raise ValueError("presupuesto_max_mxn debe estar entre 1,000 y 50,000,000")
    zona, aviso_zona = resolver_zona(str(rapido.get("destino_trabajo") or ""))
    s = SUPUESTOS_PERFIL
    if operacion == "renta":
        ingreso = max(1_000, presupuesto * s["ingreso_por_presupuesto"])
        enganche = None
    else:  # mensualidad aprox. ≤ 30% del ingreso
        enganche = int(presupuesto * s["enganche_pct"])
        ingreso = max(10_000, int(presupuesto * 0.8 * 0.0097 / 0.30))
    perfil = {
        "operacion_deseada": operacion,
        "presupuesto_max_mxn": presupuesto,
        "ingreso_mensual_mxn": min(ingreso, 2_000_000),
        "destino_trabajo": {"lat": zona["lat"], "lng": zona["lng"], "direccion": zona["nombre"]},
        "modo_transporte": s["modo_transporte"],
        "tiempo_max_traslado_min": s["tiempo_max_traslado_min"],
        "recamaras_min": 0,
        "mascotas": bool(rapido.get("mascotas")),
        "tiene_aval": False,
        "enganche_disponible_mxn": enganche,
        "prioridades": s["prioridades"],
    }
    supuestos = [
        f"Destino de trabajo: {zona['nombre']} ({zona['lat']:.4f}, {zona['lng']:.4f}).",
        f"Ingreso mensual estimado: ${perfil['ingreso_mensual_mxn']:,} (no lo preguntamos).",
        "Te mueves en transporte público y aceptas hasta 45 minutos de traslado.",
        "Prioridades: precio, luego traslado, luego comunidad.",
    ]
    if enganche is not None:
        supuestos.append(f"Enganche del 20%: ${enganche:,}.")
    if aviso_zona:
        supuestos.insert(0, aviso_zona)
    return perfil, supuestos


def _tarjeta(ctx, res: dict) -> dict:
    i = res["inmueble"]
    c = res.get("costo_real") or {}
    pj = (res.get("precio_justo") or {}).get("banda", "sin_dato")
    riesgo = (res.get("score_riesgo") or {}).get("nivel", "bajo")
    chips = []
    if c.get("total_mensual_mxn"):
        chips.append({"texto": f"Costo real ${c['total_mensual_mxn']:,}/mes", "variante": "ia"})
    if c.get("minutos_traslado") is not None:
        chips.append({"texto": f"~{c['minutos_traslado']} min al trabajo", "variante": "neutro"})
    chips.append(dict(zip(("texto", "variante"), CHIP_PRECIO.get(pj, CHIP_PRECIO["sin_dato"]))))
    chips.append(dict(zip(("texto", "variante"), CHIP_RIESGO.get(riesgo, CHIP_RIESGO["bajo"]))))
    col = ctx.colonias.get(normalizar_colonia(i["colonia"]))
    presion = col.indicador_presion_gentrificacion.valor if col else None
    if presion is not None and presion >= 0.75:
        chips.append({"texto": "Alta presión de gentrificación", "variante": "alerta"})
    com = res.get("comunidad") or {}
    info = h.info_colonia(ctx, i["colonia"])
    fuente_com = next((f.descripcion for f in info.fuentes if "OpenStreetMap" in f.descripcion or "DENUE" in f.descripcion), "OpenStreetMap / INEGI DENUE")
    fecha_com = next((str(f.fecha_dato) for f in info.fuentes if f.fecha_dato), "")
    tipo_rec = "Estudio" if i["recamaras"] == 0 else f"{i['recamaras']} rec."
    return {
        "id": i["id"],
        "titulo": f"{tipo_rec} en {'renta' if i['operacion'] == 'renta' else 'venta'}, {i.get('m2') or '?'} m²",
        "colonia": i["colonia"],
        "operacion": i["operacion"],
        "precio_mxn": i["precio_mxn"],
        "chips": chips,
        "datoComunidad": {
            "texto": (f"Cerca: {com['nombre']} ({com.get('tipo', 'lugar')})." if com.get("nombre") else info.explicacion),
            "fuente": fuente_com,
            "fecha_dato": fecha_com,
        },
        "fuente": "sintetico" if i.get("fuente") == "sintetico" else i.get("fuente"),
        "esEjemplo": i.get("fuente") == "sintetico",
        # extras para la tarjeta ampliada
        "porQue": res.get("por_que"),
        "costoReal": c,
        "precioJusto": pj,
        "riesgo": riesgo,
        "presionGentrificacion": presion,
        "ubicacionAproximada": i.get("ubicacion_aproximada", False),
        "avisos": res.get("avisos", []),
    }


def _buscar(perfil: dict, limite: int = 3) -> dict:
    ctx = contexto()
    r = h.buscar_inmuebles(ctx, perfil, limite=limite)
    resultados = r.datos.get("resultados", []) if isinstance(r.datos, dict) else []
    salida = {
        "opciones": [_tarjeta(ctx, x) for x in resultados],
        "explicacion": r.explicacion,
        "avisos": r.avisos,
        "fuentes": [{"descripcion": f.descripcion, "fecha_dato": str(f.fecha_dato or "")} for f in r.fuentes],
        "origen": "api",
    }
    if not resultados:
        salida["mensajeSinResultados"] = r.explicacion
    alt = h.alternativas_equilibradas(ctx, perfil)
    salida["alternativas"] = {"explicacion": alt.explicacion, "datos": alt.datos}
    return salida


# ---------------- rutas ----------------

async def salud(_: Request):
    ctx = contexto()
    return JSONResponse({"ok": True, "inmuebles": len(ctx.inmuebles), "colonias": len(ctx.colonias), "origen": "api"})


async def zonas(_: Request):
    return JSONResponse(ZONAS)


async def colonias(_: Request):
    ctx = contexto()
    presion = {k: c.indicador_presion_gentrificacion.valor for k, c in ctx.colonias.items()}
    with PILOTO.open(encoding="utf-8", newline="") as f:
        filas = [
            {"colonia": r["colonia"], "alcaldia": r["alcaldia"], "hipotesis_presion": r["hipotesis_presion"],
             "rol": r["rol"], "presion_gentrificacion": presion.get(normalizar_colonia(r["colonia"]))}
            for r in csv.DictReader(f)
        ]
    return JSONResponse(filas)


async def stats(_: Request):
    ctx = contexto()
    return JSONResponse({"colonias": len(ctx.colonias), "anuncios": len(ctx.inmuebles),
                         "porcentajeExplicado": 100, "origen": "api",
                         "nota": "Anuncios sintéticos de ejemplo; todas las recomendaciones traen explicación."})


async def ejemplo(_: Request):
    perfil, supuestos = perfil_completo({"operacion": "renta", "presupuesto_max_mxn": 22000,
                                         "destino_trabajo": "reforma", "mascotas": False})
    r = _buscar(perfil, limite=1)
    if not r["opciones"]:
        return JSONResponse({"error": "sin ejemplo disponible"}, status_code=404)
    return JSONResponse({**r["opciones"][0], "supuestos": supuestos})


async def buscar(request: Request):
    try:
        cuerpo = await request.json()
        perfil, supuestos = perfil_completo(cuerpo)
    except (ValueError, json.JSONDecodeError) as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    r = _buscar(perfil, limite=int(cuerpo.get("limite", 3)))
    return JSONResponse({**r, "supuestos": supuestos, "perfilUsado": perfil})


async def inmueble(request: Request):
    ctx = contexto()
    iid = request.path_params["id"]
    perfil, supuestos = perfil_completo({
        "operacion": request.query_params.get("operacion", "renta"),
        "presupuesto_max_mxn": int(request.query_params.get("presupuesto", 20000)),
        "destino_trabajo": request.query_params.get("destino", "reforma"),
        "mascotas": False,
    })
    partes = {
        "costoReal": h.costo_real(ctx, iid, perfil),
        "precioJusto": h.precio_justo(ctx, iid),
        "confiabilidad": h.score_fraude(ctx, iid),
    }
    if not partes["precioJusto"].ok:
        return JSONResponse({"error": partes["precioJusto"].explicacion}, status_code=404)
    return JSONResponse({
        "id": iid,
        **{k: {"explicacion": v.explicacion, "datos": v.datos, "avisos": v.avisos,
               "fuentes": [{"descripcion": f.descripcion, "fecha_dato": str(f.fecha_dato or "")} for f in v.fuentes]}
           for k, v in partes.items()},
        "supuestos": supuestos,
    }, )


app = Starlette(
    routes=[
        Route("/api/salud", salud),
        Route("/api/zonas", zonas),
        Route("/api/colonias", colonias),
        Route("/api/stats", stats),
        Route("/api/ejemplo", ejemplo),
        Route("/api/buscar", buscar, methods=["POST"]),
        Route("/api/inmuebles/{id}", inmueble),
    ],
    middleware=[Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])],
)
