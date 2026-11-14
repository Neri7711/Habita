"""Herramientas del agente con un contexto pequeño hecho a mano, sin red."""
import json
from datetime import date

import pytest

from arraigo.agente import herramientas as h
from arraigo.agente.contexto import ErrorDatos, cargar_contexto, construir_contexto_agente
from arraigo.agente.envoltorio import AVISO_HIPOTECA, AVISO_SINTETICO, AVISO_UBICACION
from arraigo.antifraude import ConfigReglas
from arraigo.schemas.colonia import Colonia, Dato, Punto, PuntoComunidad
from arraigo.schemas.inmueble import Inmueble

HOY = date(2026, 1, 1)
PENDIENTE = {"aviso": "pendiente spec 03"}


def dato(valor):
    return {"valor": valor, "fuente": "dato de prueba", "fecha_dato": HOY}


def colonia(nombre, presion=None, delitos=None, puntos=None, mediana_renta=None) -> Colonia:
    c = {"nombre": nombre, "alcaldia": "Alcaldía X"}
    if presion is not None:
        c["indicador_presion_gentrificacion"] = dato(presion)
    if delitos is not None:
        c["indice_delitos"] = dato(delitos)
    if puntos is not None:
        c["puntos_comunidad"] = dato(puntos)
    if mediana_renta is not None:
        c["precio_m2_renta_mediana"] = dato(mediana_renta)
    return Colonia.model_validate(c)


def punto(nombre, tipo):
    return PuntoComunidad(nombre=nombre, tipo=tipo, punto=Punto(lat=19.4, lng=-99.16), distancia_m=300)


def inm(id, colonia, precio, operacion="renta", m2=50.0, recamaras=1, **kw) -> Inmueble:
    base = dict(id=id, operacion=operacion, precio_mxn=precio, colonia=colonia, alcaldia="Alcaldía X",
                lat=19.4, lng=-99.16, m2=m2, recamaras=recamaras, banos=1, fuente="sintetico", fecha_captura=HOY,
                descripcion=f"Departamento {id}.")
    base.update(kw)
    return Inmueble(**base)


@pytest.fixture
def ctx():
    colonias = [
        colonia("Roma Norte", presion=0.8, delitos=50, mediana_renta=300,
                puntos=[punto("Mercado Medellín", "mercado"), punto(None, "parque")]),
        colonia("Narvarte Poniente", presion=0.4, delitos=20, puntos=[punto("Parque de los Venados", "parque")]),
        colonia("Álamos", presion=0.3),
        colonia("San Rafael"),
    ]
    inmuebles = [
        inm("r1", "Roma Norte", 15000),
        inm("r2", "Narvarte Poniente", 12000, m2=60, recamaras=2),
        inm("r3", "Álamos", 10000, m2=40, requisitos=["aval"]),
        inm("r4", "Narvarte Poniente", 9000, m2=45, es_fraude_prueba=True,
            descripcion="Te entrego la llave despues del deposito."),
        inm("r5", "Roma Norte", 30000),
        inm("v1", "Narvarte Poniente", 3_000_000, operacion="venta", m2=80, recamaras=2, acepta_mascotas=False),
        inm("v2", "Álamos", 2_500_000, operacion="venta", m2=70, recamaras=2, lat=None, lng=None),
    ]
    config = ConfigReglas(version=1, reglas={
        "deposito_antes_de_visitar": {"peso": 70, "frases_directas": ["\\bdespues del deposito\\b"]},
    })
    return construir_contexto_agente(inmuebles, colonias, config, generado_en=HOY)


def perfil(**kw) -> dict:
    base = dict(operacion_deseada="renta", presupuesto_max_mxn=20000, ingreso_mensual_mxn=40000,
                destino_trabajo={"lat": 19.43, "lng": -99.19}, modo_transporte="transporte_publico",
                tiempo_max_traslado_min=40, prioridades=["precio", "seguridad"])
    base.update(kw)
    return base


def perfil_compra(**kw) -> dict:
    return perfil(operacion_deseada="compra", presupuesto_max_mxn=3_200_000, enganche_disponible_mxn=640_000,
                  recamaras_min=2, mascotas=True, prioridades=["seguridad", "espacio"], **kw)


@pytest.fixture
def sin_calculos(monkeypatch):
    monkeypatch.setattr(h, "_funcion_calculos", lambda nombre: None)


def _costo_falso(inmueble, perfil, colonia):
    minutos = 60 if inmueble.id == "r1" else 25
    comp = lambda m: {"monto_mxn": m, "fuente": "tabla de prueba", "fecha_dato": "2026-01-01",
                      "supuestos": [f"supuesto de {m}"]}
    d = {"inmueble_id": inmueble.id, "vivienda": comp(inmueble.precio_mxn if inmueble.operacion.value == "renta" else 20000),
         "transporte": comp(800), "servicios": comp(1200), "tiempo_valorizado": comp(1500),
         "costo_real_mxn": 3500 + (inmueble.precio_mxn if inmueble.operacion.value == "renta" else 20000),
         "costo_monetario_mxn": 2000, "avisos": [],
         "traslado": {"distancia_recta_km": 5.0, "distancia_ruta_km": 6.5, "minutos_ida": minutos}}
    if inmueble.operacion.value == "venta":
        d["hipoteca"] = {"tasa_anual_pct": 11.5, "plazo_anios": 20, "enganche_mxn": 640000,
                         "fuente_tasa": "Banxico SIE (prueba)", "fecha_tasa": "2026-01-01"}
    return d


def _precio_justo_falso(banda):
    def f(inmueble, colonia):
        return {"banda": banda, "precio_m2": 200.0, "mediana_m2": 400.0, "razon": 0.5,
                "fuente_referencia": "mediana de anuncios capturados (n=3), Roma Norte, 2026-01-01",
                "n_anuncios_mediana": 3, "motivo_no_evaluable": "sin m2" if banda == "no_evaluable" else None}
    return f


@pytest.fixture
def con_calculos(monkeypatch):
    funciones = {"costo_real": _costo_falso, "precio_justo": _precio_justo_falso("justo")}
    monkeypatch.setattr(h, "_funcion_calculos", lambda nombre: funciones.get(nombre))
    return funciones


def _texto(env) -> str:
    return json.dumps(env.model_dump(mode="json"), ensure_ascii=False)


# ---------------- contexto ----------------

def test_faltan_archivos_da_error_con_comando(tmp_path):
    with pytest.raises(ErrorDatos, match="scripts/cargar_dataset.py"):
        cargar_contexto(tmp_path)


# ---------------- buscar_inmuebles ----------------

def test_buscar_filtra_ordena_y_excluye_riesgo_alto(ctx, sin_calculos):
    env = h.buscar_inmuebles(ctx, perfil())
    assert env.ok
    ids = [r["inmueble"]["id"] for r in env.datos["resultados"]]
    assert ids == ["r2", "r1"]  # r3 pide aval, r4 riesgo alto, r5 fuera de presupuesto
    assert env.datos["excluidos_por_riesgo"] == 1
    primero = env.datos["resultados"][0]
    assert primero["costo_real"] == PENDIENTE and primero["precio_justo"] == PENDIENTE
    assert primero["score_riesgo"]["nivel"] == "bajo"
    assert primero["comunidad"] == {"nombre": "Parque de los Venados", "tipo": "parque"}
    assert primero["por_que"].startswith("Quedó en el lugar 1 porque")
    assert AVISO_SINTETICO in env.avisos
    assert any("pendiente spec 03" in a for a in env.avisos)


def test_buscar_con_aval_incluye_y_avisa_dato_faltante(ctx, sin_calculos):
    env = h.buscar_inmuebles(ctx, perfil(tiene_aval=True))
    r3 = next(r for r in env.datos["resultados"] if r["inmueble"]["id"] == "r3")
    assert any("índice de delitos" in a and "r3" in a for a in r3["avisos"])
    assert r3["desglose"]["seguridad"] == pytest.approx(100 * (0.25 / 0.60) * 0.5, abs=0.01)


def test_buscar_mascotas_y_ubicacion_aproximada(ctx, sin_calculos):
    env = h.buscar_inmuebles(ctx, perfil_compra())
    ids = [r["inmueble"]["id"] for r in env.datos["resultados"]]
    assert ids == ["v2"]  # v1 no acepta mascotas
    assert AVISO_UBICACION in env.avisos


def test_buscar_sin_resultados_sugiere_filtro(ctx, sin_calculos):
    env = h.buscar_inmuebles(ctx, perfil(presupuesto_max_mxn=1000))
    assert env.ok and env.datos["resultados"] == []
    assert env.datos["filtro_mas_restrictivo"] == "presupuesto"
    assert "presupuesto" in env.explicacion


def test_buscar_entrada_invalida(ctx):
    env = h.buscar_inmuebles(ctx, perfil(prioridades=["precio", "precio"]))
    assert not env.ok and "prioridades: no puede tener repetidos" in env.error
    env = h.buscar_inmuebles(ctx, perfil(), limite=11)
    assert not env.ok and "limite" in env.error


def test_buscar_con_calculos_filtra_traslado(ctx, con_calculos):
    env = h.buscar_inmuebles(ctx, perfil())
    ids = [r["inmueble"]["id"] for r in env.datos["resultados"]]
    assert ids == ["r2"]  # r1 tarda 60 min > 40
    assert env.datos["descartados_por_filtro"]["traslado"] == 1
    assert env.datos["resultados"][0]["costo_real"]["total_mensual_mxn"] == 15500
    assert env.datos["resultados"][0]["precio_justo"] == {"banda": "justo"}


# ---------------- costo_real ----------------

def test_costo_real_pendiente(ctx, sin_calculos):
    env = h.costo_real(ctx, "r2", perfil())
    assert env.ok and env.datos == PENDIENTE


def test_costo_real_con_adaptador(ctx, con_calculos):
    env = h.costo_real(ctx, "v2", perfil_compra())
    assert env.ok
    assert env.datos["total_mensual_mxn"] == 23500
    assert AVISO_HIPOTECA in env.avisos
    assert "Modo de transporte: transporte_publico" in env.explicacion
    assert "Factor de rodeo: 1.30" in env.explicacion
    assert "Tasa anual: 11.50%" in env.explicacion
    assert any("Banxico" in f.descripcion for f in env.fuentes)


def test_costo_real_id_inexistente(ctx, con_calculos):
    env = h.costo_real(ctx, "r22", perfil())
    assert not env.ok and env.datos["ids_parecidos"]


# ---------------- precio_justo ----------------

def test_precio_justo_pendiente(ctx, sin_calculos):
    assert h.precio_justo(ctx, "r1").datos == PENDIENTE


def test_precio_justo_barato_remite_a_score_fraude(ctx, con_calculos, monkeypatch):
    con_calculos["precio_justo"] = _precio_justo_falso("sospechosamente_barato")
    env = h.precio_justo(ctx, "r1")
    assert env.datos["banda"] == "sospechosamente_barato"
    assert "score_fraude" in env.explicacion
    assert any("pocos anuncios" in a for a in env.avisos)


def test_precio_justo_sin_dato(ctx, con_calculos):
    con_calculos["precio_justo"] = _precio_justo_falso("no_evaluable")
    env = h.precio_justo(ctx, "r1")
    assert env.datos["banda"] == "sin_dato"
    assert "No podemos decir" in env.explicacion


# ---------------- score_fraude ----------------

def test_score_fraude_no_expone_etiqueta(ctx):
    env = h.score_fraude(ctx, "r4")
    assert env.datos["nivel"] == "alto"
    assert "es_fraude_prueba" not in _texto(env)


def test_score_fraude_sin_senales_no_garantiza(ctx):
    env = h.score_fraude(ctx, "r2")
    assert env.datos["nivel"] == "bajo" and "no garantiza" in env.explicacion


# ---------------- info_colonia ----------------

@pytest.mark.parametrize("texto", ["roma norte", "ROMA NORTE", "Col. Roma Norte", "roma"])
def test_info_colonia_normaliza(ctx, texto):
    env = h.info_colonia(ctx, texto)
    assert env.datos["nombre"] == "Roma Norte"


def test_info_colonia_contenido(ctx):
    env = h.info_colonia(ctx, "Roma Norte")
    assert "Mercado Medellín" in env.explicacion
    assert "alternativas_equilibradas" in env.explicacion
    assert env.datos["campos"]["nivel_riesgo"] == "sin dato"
    assert env.datos["campos"]["indice_delitos"]["fuente"] == "dato de prueba"
    assert any("nivel de riesgo" in a for a in env.avisos)


def test_info_colonia_acentos_y_sin_puntos(ctx):
    env = h.info_colonia(ctx, "alamos")
    assert env.datos["nombre"] == "Álamos"
    assert "No tenemos datos de lugares de comunidad" in env.explicacion


@pytest.mark.parametrize("texto", ["o", "Polanco"])
def test_info_colonia_ambigua_o_inexistente(ctx, texto):
    env = h.info_colonia(ctx, texto)
    assert len(env.datos["colonias_disponibles"]) == 4


# ---------------- alternativas_equilibradas ----------------

def test_alternativas_menor_presion(ctx, sin_calculos):
    env = h.alternativas_equilibradas(ctx, perfil(tiene_aval=True), "Roma Norte")
    alts = env.datos["alternativas"]
    assert 1 <= len(alts) <= 3
    assert all(a["presion_gentrificacion"] < 0.8 for a in alts)
    assert {a["colonia"] for a in alts} == {"Narvarte Poniente", "Álamos"}
    comp = alts[0]["comparacion_con_origen"]
    assert comp["referencia_origen"] == "r1" and comp["diferencia_presion"] < 0
    assert "Roma Norte tiene una presión alta" in env.explicacion
    assert any("San Rafael" in a for a in env.avisos)


def test_alternativas_sin_resultados_no_rellena(ctx, sin_calculos):
    env = h.alternativas_equilibradas(ctx, perfil(presupuesto_max_mxn=1000), "Roma Norte")
    assert env.datos["alternativas"] == []
    assert "No encontramos alternativas" in env.explicacion


def test_alternativas_origen_sin_presion_alta(ctx, sin_calculos):
    env = h.alternativas_equilibradas(ctx, perfil(tiene_aval=True), "Narvarte Poniente")
    assert [a["colonia"] for a in env.datos["alternativas"]] == ["Álamos"]
    assert "no es una colonia de alta presión" in env.explicacion


def test_alternativas_origen_desconocido(ctx, sin_calculos):
    env = h.alternativas_equilibradas(ctx, perfil(), "Polanco")
    assert not env.ok and "colonia_origen" in env.error


# ---------------- reglas transversales ----------------

def test_ninguna_salida_dice_estafa_ni_expone_etiqueta(ctx, con_calculos):
    salidas = [
        h.buscar_inmuebles(ctx, perfil(tiene_aval=True)),
        h.buscar_inmuebles(ctx, perfil_compra()),
        h.costo_real(ctx, "r4", perfil()),
        h.precio_justo(ctx, "r4"),
        h.score_fraude(ctx, "r4"),
        h.info_colonia(ctx, "Roma Norte"),
        h.alternativas_equilibradas(ctx, perfil(tiene_aval=True), "Roma Norte"),
    ]
    for env in salidas:
        texto = _texto(env).lower()
        assert "estafa" not in texto and "fraude confirmado" not in texto
        assert "es_fraude_prueba" not in texto
