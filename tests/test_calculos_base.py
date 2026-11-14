"""Datos fijos de prueba para la spec 03. No lee `data/raw/` (design.md, estrategia de pruebas)."""
from __future__ import annotations

from datetime import date

from arraigo.calculos.modelos import TasaReferencia
from arraigo.calculos.supuestos import ConfigCalculos, TarifasSemovi
from arraigo.schemas import Colonia, Dato, Inmueble, Perfil

F = "2026-01-01"
FUENTE = "prueba"

CONFIG = ConfigCalculos.model_validate(
    {
        "traslado": {
            "factor_rodeo": {"transporte_publico": 1.4, "auto": 1.3, "bici": 1.25},
            "velocidad_kmh": {"transporte_publico": 17, "auto": 22, "bici": 14},
            "fuente": FUENTE, "fecha_dato": F,
        },
        "calendario": {"dias_laborales_mes": 22, "horas_laborales_dia": 8, "viajes_por_dia": 2, "fuente": FUENTE, "fecha_dato": F},
        "pasajes": {
            "tramos": [{"hasta_km": 10, "pasajes": 1}, {"hasta_km": 20, "pasajes": 2}, {"hasta_km": None, "pasajes": 3}],
            "fuente": FUENTE, "fecha_dato": F,
        },
        "transporte_publico": {
            "tarifa_por_defecto": "metro",
            "mapeo_estacion": {"metro": "metro", "metrobus": "metrobus", "cablebus": "cablebus"},
            "fuente": FUENTE, "fecha_dato": F,
        },
        "auto": {"costo_por_km_mxn": 3.0, "nota": "combustible y mantenimiento", "fuente": FUENTE, "fecha_dato": F},
        "tiempo": {"factor_valor_tiempo": 1.0, "fuente": FUENTE, "fecha_dato": F},
        "servicios": {
            "base_mxn": 900, "por_recamara_mxn": 250,
            "desglose_pct": {"luz": 0.30, "agua": 0.15, "gas": 0.25, "internet": 0.30},
            "fuente": "supuesto del equipo", "fecha_dato": F,
        },
        "compra": {
            "mantenimiento_predial_anual_pct": 0.006, "plazo_anios": 20, "enganche_minimo_pct": 0.10,
            "spread_sobre_tiie_pp": 3.5, "tasa_respaldo_anual_pct": 11.5, "serie_banxico": "SF43783",
            "pago_max_pct_ingreso": 0.35, "fuente": FUENTE, "fecha_dato": F,
        },
        "precio_justo": {"umbral_sospechosamente_barato": 0.70, "umbral_caro": 1.15, "fuente": FUENTE, "fecha_dato": F},
    }
)


def _tarifa(mxn: float, cobro: str = "viaje") -> dict:
    return {"mxn": mxn, "tipo_cobro": cobro, "url": "https://ejemplo.mx/tarifa", "fecha_vigencia": F}


TARIFAS = TarifasSemovi.model_validate(
    {
        "tarifas": {
            "metro": _tarifa(5), "metrobus": _tarifa(6), "trolebus": _tarifa(4), "tren_ligero": _tarifa(3),
            "rtp": _tarifa(2), "cablebus": _tarifa(7), "ecobici_anual": _tarifa(600, "anual"),
        }
    }
)

TASA = TasaReferencia(tasa_pct=8.0, fecha=date(2026, 1, 1), fuente="Banco de México, SIE, serie SF43783")

# Un grado de latitud ≈ 111.195 km; 6.0 km en línea recta hacia el norte desde (19.40, -99.16).
LAT0, LNG0 = 19.40, -99.16
LAT_6KM = LAT0 + 6.0 / 111.19508


def inmueble(**kw) -> Inmueble:
    base = dict(
        id="t-1", operacion="renta", precio_mxn=18_000, colonia="Roma Norte", alcaldia="Cuauhtémoc",
        lat=LAT0, lng=LNG0, m2=60.0, recamaras=2, banos=1.0, fuente="captura_manual", fecha_captura=date(2026, 1, 1),
    )
    base.update(kw)
    return Inmueble(**base)


def perfil(**kw) -> Perfil:
    base = dict(
        operacion_deseada="renta", presupuesto_max_mxn=25_000, ingreso_mensual_mxn=30_000,
        destino_trabajo={"lat": LAT_6KM, "lng": LNG0, "direccion": "Trabajo"},
        modo_transporte="transporte_publico", tiempo_max_traslado_min=45, prioridades=["precio"],
    )
    base.update(kw)
    return Perfil(**base)


def colonia(renta_m2: float | None = 360.0, venta_m2: float | None = None, fuente: str = "Mediana de anuncios capturados (n=12)",
            **kw) -> Colonia:
    def dato(v):
        return Dato[float](valor=v, fuente=fuente, fecha_dato=date(2026, 1, 1)) if v is not None else Dato[float]()

    return Colonia(
        nombre="Roma Norte", alcaldia="Cuauhtémoc",
        precio_m2_renta_mediana=dato(renta_m2), precio_m2_venta_mediana=dato(venta_m2), **kw,
    )
