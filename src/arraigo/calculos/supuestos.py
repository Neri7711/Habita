"""Supuestos fijos de la spec 03 (versión mínima para el demo).

shortcut: constantes en código en vez de calculos_supuestos.json / tarifas_semovi.json y tasa fija en vez de Banxico;
pasar a archivos con fuente por valor si hay tiempo después del demo.
"""

from datetime import date

FUENTE = "Supuesto del equipo (spec 03), a validar"
FECHA = date(2026, 11, 14)

FACTOR_RODEO = {"transporte_publico": 1.4, "auto": 1.3, "bici": 1.25}
VELOCIDAD_KMH = {"transporte_publico": 17, "auto": 22, "bici": 14}
DIAS_LABORALES_MES = 22
HORAS_LABORALES_DIA = 8
# (hasta_km de ruta, pasajes por viaje) para aproximar transbordos
PASAJES_POR_DISTANCIA = [(10, 1), (20, 2), (float("inf"), 3)]
TARIFA_METRO_MXN = 5  # tarifa del Metro CDMX
FUENTE_TARIFA = "Tarifa del Metro CDMX ($5 por viaje), STC Metro"
ECOBICI_ANUAL_MXN = 521  # por verificar
AUTO_COSTO_POR_KM_MXN = 3.0  # combustible + mantenimiento
FACTOR_VALOR_TIEMPO = 1.0
SERVICIOS_BASE_MXN = 900
SERVICIOS_POR_RECAMARA_MXN = 250
MANTENIMIENTO_PREDIAL_ANUAL_PCT = 0.006
TASA_HIPOTECARIA_ANUAL_PCT = 11.5  # fija: TIIE aproximada + spread; no es dato de Banxico
PLAZO_ANIOS = 20
UMBRAL_BARATO = 0.70  # coincide con precio_algo_bajo de antifraude
UMBRAL_CARO = 1.15

AVISO_GENERAL = "Estimación con supuestos; revisa los detalles antes de decidir."
AVISO_COMPRA = ("Estimación, no es asesoría hipotecaria; tasa fija de referencia, no incluye comisiones, "
                "seguros ni gastos de escrituración.")
AVISO_APROX = "Ubicación aproximada: el traslado puede variar."
AVISO_SINTETICO = "Este anuncio es sintético (de prueba), no un inmueble real."
AVISO_MIXTO = "Para modo mixto se usó el cálculo de transporte público."
AVISO_AUTO = "No incluye estacionamiento, seguro ni tenencia."
