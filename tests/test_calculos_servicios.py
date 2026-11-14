from arraigo.calculos.servicios import costo_servicios
from test_calculos_base import CONFIG, inmueble


def test_servicios_renta_ejemplo_del_diseno():
    c = costo_servicios(inmueble(), CONFIG)
    assert c.monto_mxn == 1400  # 900 + 250 × 2
    assert c.fuente == "supuesto del equipo"
    assert c.desglose == {"luz": 420, "agua": 210, "gas": 350, "internet": 420}
    assert any("Estimación, no una cotización" in s for s in c.supuestos)


def test_servicios_sin_recamaras():
    assert costo_servicios(inmueble(recamaras=0), CONFIG).monto_mxn == 900


def test_venta_suma_mantenimiento_y_predial():
    c = costo_servicios(inmueble(operacion="venta", precio_mxn=3_000_000), CONFIG)
    # 3,000,000 × 0.6% / 12 = 1,500
    assert c.desglose["mantenimiento_y_predial"] == 1500
    assert c.monto_mxn == 2900
