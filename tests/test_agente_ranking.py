from datetime import date

import pytest

from arraigo.agente.ranking import (
    NEUTRO,
    Candidato,
    filtros_duros,
    normalizar_min_max,
    pesos,
    puntuar,
)
from arraigo.schemas.colonia import Colonia, Dato
from arraigo.schemas.inmueble import Inmueble
from arraigo.schemas.perfil import Perfil

HOY = date(2026, 1, 1)


def inm(id, colonia="A", precio=10000, m2=50.0, operacion="renta", **kw) -> Inmueble:
    base = dict(id=id, operacion=operacion, precio_mxn=precio, colonia=colonia, alcaldia="X", lat=19.4, lng=-99.15,
                m2=m2, recamaras=1, banos=1, fuente="sintetico", fecha_captura=HOY)
    base.update(kw)
    return Inmueble(**base)


def col(nombre, delitos=None) -> Colonia:
    d = Dato[float](valor=delitos, fuente="prueba", fecha_dato=HOY) if delitos is not None else Dato[float]()
    return Colonia(nombre=nombre, alcaldia="X", indice_delitos=d)


def perfil(**kw) -> Perfil:
    base = dict(operacion_deseada="renta", presupuesto_max_mxn=20000, ingreso_mensual_mxn=40000,
                destino_trabajo={"lat": 19.43, "lng": -99.19}, modo_transporte="transporte_publico",
                tiempo_max_traslado_min=60, prioridades=["precio"])
    base.update(kw)
    return Perfil(**base)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_pesos_suman_uno_y_primera_pesa_mas(n):
    prios = ["precio", "traslado", "seguridad", "comunidad", "espacio"][:n]
    w = pesos(prios)
    assert sum(w.values()) == pytest.approx(1.0)
    assert w[prios[0]] == max(w.values())
    assert list(w.values()) == sorted(w.values(), reverse=True)


def test_pesos_tres_prioridades():
    w = pesos(["precio", "traslado", "seguridad"])
    assert w == pytest.approx({"precio": 0.4375, "traslado": 0.3125, "seguridad": 0.25})


def test_normalizacion_min_max():
    assert normalizar_min_max({"a": 10, "b": 20}) == {"a": 0.0, "b": 1.0}
    assert normalizar_min_max({"a": 10, "b": 20}, invertir=True) == {"a": 1.0, "b": 0.0}
    assert normalizar_min_max({"a": 7, "b": 7}) == {"a": NEUTRO, "b": NEUTRO}
    assert normalizar_min_max({"a": 1, "b": None, "c": 3}) == {"a": 0.0, "b": None, "c": 1.0}


def test_filtros_duros_cuentan_el_primero_que_falla():
    p = perfil(recamaras_min=1, mascotas=True)
    items = [
        inm("ok"),
        inm("venta", operacion="venta", precio=1_000_000),
        inm("caro", precio=30000),
        inm("chico", recamaras=0),
        inm("sin_mascotas", acepta_mascotas=False),
        inm("aval", requisitos=["aval"]),
        inm("mascota_desconocida", acepta_mascotas=None),
    ]
    pasan, conteo = filtros_duros(items, p)
    assert [i.id for i in pasan] == ["ok", "mascota_desconocida"]
    assert conteo == {"operacion": 1, "presupuesto": 1, "recamaras": 1, "mascotas": 1, "aval": 1}


def test_aval_no_aplica_si_tiene_aval():
    pasan, _ = filtros_duros([inm("aval", requisitos=["aval"])], perfil(tiene_aval=True))
    assert len(pasan) == 1


def test_menor_precio_gana_con_prioridad_precio():
    cands = [Candidato(inm("a", precio=15000), col("A"), 15000, None),
             Candidato(inm("b", precio=10000), col("A"), 10000, None)]
    r = puntuar(cands, ["precio"], [col("A")])
    assert [x.id for x in r] == ["b", "a"]
    assert r[0].puntuacion == 100 and r[1].puntuacion == 0


def test_dato_faltante_vale_neutro_y_se_reporta():
    colonias = [col("A", 10), col("B", 30), col("C")]
    cands = [Candidato(inm("a", "A"), colonias[0], 10000, None),
             Candidato(inm("c", "C"), colonias[2], 10000, None)]
    r = {x.id: x for x in puntuar(cands, ["seguridad", "traslado"], colonias)}
    assert r["a"].criterios["seguridad"] == 1.0
    assert r["c"].criterios["seguridad"] == NEUTRO and "seguridad" in r["c"].faltantes
    assert all("traslado" in x.faltantes for x in r.values())


def test_empate_se_desempata_por_id_y_es_determinista():
    cands = [Candidato(inm(i), col("A"), 10000, 20) for i in ("z", "m", "a")]
    r1 = [x.id for x in puntuar(cands, ["precio", "traslado"], [col("A")])]
    r2 = [x.id for x in puntuar(list(reversed(cands)), ["precio", "traslado"], [col("A")])]
    assert r1 == r2 == ["a", "m", "z"]


def test_precio_se_normaliza_por_operacion():
    cands = [Candidato(inm("r1", precio=10000), col("A"), 10000, None),
             Candidato(inm("r2", precio=20000), col("A"), 20000, None),
             Candidato(inm("v1", operacion="venta", precio=2_000_000), col("A"), 15000, None)]
    r = {x.id: x for x in puntuar(cands, ["precio"], [col("A")])}
    # v1 es el único de venta: no compite contra las rentas.
    assert r["v1"].criterios["precio"] == NEUTRO
    assert r["r1"].criterios["precio"] == 1.0
