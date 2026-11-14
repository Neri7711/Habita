from arraigo.calculos.supuestos import Tramo
from arraigo.calculos.traslado import estimar_traslado
from arraigo.calculos.transporte import costo_transporte_mensual
from arraigo.schemas import Dato
from arraigo.schemas.colonia import Estacion, Modo, Punto
from test_calculos_base import CONFIG, TARIFAS, colonia, inmueble, perfil


def _costo(modo="transporte_publico", col=None, **kw_inm):
    p = perfil(modo_transporte=modo)
    t = estimar_traslado(inmueble(**kw_inm), p, CONFIG)
    return costo_transporte_mensual(t, modo, col, CONFIG, TARIFAS), t


def _col_con_estacion(tipo: Modo, distancia: float = 300.0, nombre: str = "E"):
    est = Estacion(nombre=nombre, tipo=tipo, punto=Punto(lat=19.4, lng=-99.16), distancia_m=distancia)
    return colonia(estaciones_transporte_cercanas=Dato[list[Estacion]](valor=[est], fuente="GTFS", fecha_dato="2026-01-01"))


def test_transporte_publico_ejemplo_del_diseno():
    c, _ = _costo()
    assert c.monto_mxn == 220  # 1 pasaje × $5 × 2 × 22
    assert any("tarifa por defecto" in s for s in c.supuestos)
    assert c.fecha_dato.isoformat() == "2026-01-01" and c.fuente.startswith("https://")


def test_pasajes_por_tramos_de_distancia():
    assert CONFIG.pasajes.pasajes_para(10.0) == 1
    assert CONFIG.pasajes.pasajes_para(10.01) == 2
    assert CONFIG.pasajes.pasajes_para(20.0) == 2
    assert CONFIG.pasajes.pasajes_para(35.0) == 3
    assert Tramo(hasta_km=None, pasajes=3).pasajes == 3


def test_tarifa_del_tipo_de_la_estacion_mas_cercana():
    c, _ = _costo(col=_col_con_estacion(Modo.cablebus))
    assert c.monto_mxn == 308  # 1 × $7 × 2 × 22
    assert not any("tarifa por defecto" in s for s in c.supuestos)


def test_estacion_ecobici_o_sin_mapeo_usa_tarifa_por_defecto():
    c, _ = _costo(col=_col_con_estacion(Modo.ecobici))
    assert c.monto_mxn == 220


def test_tres_pasajes_en_ruta_larga():
    # 20 km en línea recta × 1.4 = 28 km de ruta → 3 pasajes
    c, t = _costo(lat=19.40 - 20.0 / 111.19508)
    assert t.distancia_ruta_km > 20 and c.monto_mxn == 660  # 3 × 5 × 2 × 22


def test_auto_costo_por_km():
    c, t = _costo("auto")
    assert c.monto_mxn == round(t.distancia_ruta_km * 2 * 22 * 3.0)  # 7.8 × 132 = 1030
    assert c.monto_mxn == 1030
    assert any("$3 por kilómetro" in s for s in c.supuestos)


def test_bici_usa_la_anualidad_de_ecobici_entre_12():
    c, _ = _costo("bici")
    assert c.monto_mxn == 50  # 600 / 12


def test_sin_traslado_no_es_calculable():
    c = costo_transporte_mensual(None, "transporte_publico", None, CONFIG, TARIFAS)
    assert c.monto_mxn is None and c.motivo_no_calculable == "sin ubicación"
