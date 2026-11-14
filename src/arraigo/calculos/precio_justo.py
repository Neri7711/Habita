"""Precio justo: precio/m2 contra la mediana de la colonia, en tres bandas."""

from __future__ import annotations

from arraigo.calculos import supuestos as S
from arraigo.schemas import Colonia, Inmueble


def precio_justo(inmueble: Inmueble, colonia: Colonia | None) -> dict:
    """Banda: sospechosamente_barato (< 0.70), justo (0.70-1.15), caro (> 1.15) o no_evaluable."""
    op = inmueble.operacion.value
    dato = None
    if colonia is not None:
        dato = colonia.precio_m2_renta_mediana if op == "renta" else colonia.precio_m2_venta_mediana
    base = {"banda": "no_evaluable", "precio_m2": None, "mediana_m2": None, "razon": None, "diferencia_pct": None,
            "fuente_referencia": None, "fecha_referencia": None, "es_sintetico": inmueble.fuente == "sintetico"}
    if not inmueble.m2:
        return base | {"explicacion": "No se puede evaluar: el anuncio no dice cuántos m² tiene."}
    if dato is None or not dato.valor:
        return base | {"explicacion": f"No se puede evaluar: no hay precio de referencia de {op} para {inmueble.colonia}."}

    precio_m2 = inmueble.precio_mxn / inmueble.m2
    razon = precio_m2 / dato.valor
    banda = "sospechosamente_barato" if razon < S.UMBRAL_BARATO else "caro" if razon > S.UMBRAL_CARO else "justo"
    dif = round((razon - 1) * 100)
    comparacion = f"{abs(dif)}% {'más barato' if dif < 0 else 'más caro'} que" if dif else "igual a"
    explicacion = (f"Cuesta ${precio_m2:,.0f} por m², {comparacion} la referencia de {inmueble.colonia} "
                   f"(${dato.valor:,.0f} por m²; {dato.fuente}, {dato.fecha_dato}).")
    if banda == "sospechosamente_barato":
        explicacion += " Un precio tan bajo puede ser señal de fraude: revisa el score de fraude."
    return base | {
        "banda": banda, "precio_m2": round(precio_m2, 1), "mediana_m2": dato.valor, "razon": round(razon, 3),
        "diferencia_pct": dif, "fuente_referencia": dato.fuente, "fecha_referencia": str(dato.fecha_dato),
        "explicacion": explicacion,
    }
