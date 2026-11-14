"""Generador de anuncios sintéticos calibrados por colonia (tarea 3.2)."""

from __future__ import annotations

import csv
import math
import random
import statistics
from pathlib import Path

from arraigo.pipeline.colonias import normalizar

COLUMNAS = [
    "id", "operacion", "precio_mxn", "colonia", "alcaldia", "lat", "lng", "ubicacion_aproximada",
    "m2", "recamaras", "banos", "estacionamiento", "acepta_mascotas", "amueblado", "requisitos",
    "descripcion", "fuente", "fecha_captura", "url_origen", "es_fraude_prueba",
]
FECHA = "2026-11-14"  # fija para que la salida sea reproducible

# PROVISIONAL - reemplazar con medianas reales. MXN por m2: (renta mensual, venta), estimación del equipo.
MEDIANAS_PROVISIONALES = {
    "roma norte": (340, 72_000),
    "hipodromo": (330, 70_000),
    "juarez": (320, 65_000),
    "escandon i seccion": (290, 58_000),
    "san rafael": (250, 45_000),
    "santa maria la ribera": (230, 42_000),
    "tacubaya": (220, 40_000),
    "narvarte poniente": (260, 52_000),
    "del valle centro": (280, 58_000),
    "portales norte": (220, 45_000),
    "alamos": (210, 43_000),
    "moctezuma 2a seccion": (170, 30_000),
    "lindavista": (190, 35_000),
}
M2_POR_RECAMARAS = {0: 35, 1: 50, 2: 75, 3: 110, 4: 150}
PATRONES_FRAUDE = ["precio_bajo", "deposito_antes", "sin_direccion", "whatsapp_extranjero", "duplicada"]


def medianas_reales(ruta: Path) -> dict[tuple[str, str], float]:
    """{(colonia_normalizada, operacion): mediana precio/m2} de los anuncios capturados a mano."""
    if not ruta.exists():
        return {}
    grupos: dict[tuple[str, str], list[float]] = {}
    with ruta.open(encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            try:
                valor = float(fila["precio_mxn"]) / float(fila["m2"])
            except (ValueError, ZeroDivisionError):
                continue
            grupos.setdefault((normalizar(fila["colonia"]), fila["operacion"]), []).append(valor)
    return {k: statistics.median(v) for k, v in grupos.items()}


def _mediana(colonia: str, operacion: str, reales: dict) -> float:
    clave = normalizar(colonia)
    if (clave, operacion) in reales:
        return reales[(clave, operacion)]
    renta, venta = MEDIANAS_PROVISIONALES[clave]
    return renta if operacion == "renta" else venta


def generar(catalogo: dict[str, dict], reales: dict | None = None, n: int = 300, seed: int = 42,
            n_fraudes: int = 25) -> list[dict]:
    rng = random.Random(seed)
    reales = reales or {}
    colonias = sorted(catalogo.values(), key=lambda c: c["colonia"])
    filas = []
    for i in range(n):
        col = colonias[i % len(colonias)]
        # 3 de cada 5 vueltas por colonia son renta → ~60/40 y todas las colonias con ambas operaciones.
        operacion = "renta" if (i // len(colonias)) % 5 < 3 else "venta"
        recamaras = rng.choice([0, 1, 1, 2, 2, 2, 3, 3, 4])
        m2 = round(M2_POR_RECAMARAS[recamaras] * rng.uniform(0.85, 1.2), 1)
        precio_m2 = _mediana(col["colonia"], operacion, reales) * rng.lognormvariate(0, 0.2)
        paso = 100 if operacion == "renta" else 10_000
        precio = max(paso, round(m2 * precio_m2 / paso) * paso)
        # Punto uniforme en un disco de 600 m alrededor del centroide.
        r, ang = 600 * math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
        lat = col["lat"] + r * math.cos(ang) / 111_320
        lng = col["lng"] + r * math.sin(ang) / (111_320 * math.cos(math.radians(col["lat"])))
        sin_coords = rng.random() < 0.05
        if operacion == "renta":
            requisitos = rng.choice([["aval"], ["poliza"], ["aval", "deposito_extra"], ["poliza", "deposito_extra"], ["ninguno"]])
        else:
            requisitos = ["ninguno"]
        tipo = "Estudio" if recamaras == 0 else f"Departamento de {recamaras} recámara{'s' if recamaras > 1 else ''}"
        filas.append({
            "id": f"sint-{i + 1:04d}",
            "operacion": operacion,
            "precio_mxn": precio,
            "colonia": col["colonia"],
            "alcaldia": col["alcaldia"],
            "lat": "" if sin_coords else round(lat, 6),
            "lng": "" if sin_coords else round(lng, 6),
            "ubicacion_aproximada": "false",
            "m2": m2,
            "recamaras": recamaras,
            "banos": 1 + (recamaras // 2) + rng.choice([0, 0.5]),
            "estacionamiento": rng.choice([0, 0, 1, 1, 2]),
            "acepta_mascotas": rng.choice(["true", "false", ""]),
            "amueblado": rng.choice(["true", "false", "false", ""]),
            "requisitos": ";".join(requisitos),
            "descripcion": f"{tipo} en {operacion} en {col['colonia']}, {m2} m2. Cerca de comercios y transporte.",
            "fuente": "sintetico",
            "fecha_captura": FECHA,
            "url_origen": "",
            "es_fraude_prueba": "false",
        })
    for k, idx in enumerate(rng.sample(range(n), n_fraudes)):
        _inyectar_fraude(filas[idx], PATRONES_FRAUDE[k % len(PATRONES_FRAUDE)], filas, rng)
    return filas


def _inyectar_fraude(fila: dict, patron: str, filas: list[dict], rng: random.Random) -> None:
    fila["es_fraude_prueba"] = "true"
    if patron == "precio_bajo":
        fila["precio_mxn"] = max(100, int(fila["precio_mxn"] * rng.uniform(0.3, 0.45)))
        fila["descripcion"] += " ¡Precio de remate, urge!"
    elif patron == "deposito_antes":
        fila["descripcion"] += " Para apartar deposita antes de ver el departamento, hay muchos interesados."
        fila["requisitos"] = "deposito_extra"
    elif patron == "sin_direccion":
        fila["lat"] = fila["lng"] = ""
        fila["descripcion"] = "Sin fotos. La dirección se da después del depósito."
    elif patron == "whatsapp_extranjero":
        fila["descripcion"] += " Contacto solo por WhatsApp +44 7700 900123, estoy fuera del país."
    elif patron == "duplicada":
        otra = rng.choice([f for f in filas if f is not fila])
        fila["descripcion"] = otra["descripcion"]


def escribir_csv(filas: list[dict], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
