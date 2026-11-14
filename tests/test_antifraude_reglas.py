from datetime import date

import pytest

from arraigo.antifraude.duplicados import IndiceDuplicados
from arraigo.antifraude.modelos import ContextoAntifraude, NoEvaluable, Senal, cargar_config
from arraigo.antifraude.reglas import REGISTRO
from arraigo.antifraude.texto import ocultar_telefono
from arraigo.schemas.colonia import Dato
from arraigo.schemas.inmueble import Inmueble, Operacion


def anuncio(**kw) -> Inmueble:
    base = dict(
        id="t1", operacion="renta", precio_mxn=20000, colonia="Roma Norte", alcaldia="Cuauhtémoc",
        lat=19.42, lng=-99.16, m2=50.0, recamaras=1, banos=1, descripcion="Departamento luminoso en Roma Norte.",
        fuente="sintetico", fecha_captura=date(2026, 1, 1),
    )
    base.update(kw)
    return Inmueble(**base)


@pytest.fixture
def ctx() -> ContextoAntifraude:
    med = Dato[float](valor=400.0, fuente="anuncios de prueba", fecha_dato=date(2026, 1, 1))
    return ContextoAntifraude(
        medianas_m2={("roma norte", Operacion.renta): med}, indice_duplicados=IndiceDuplicados(), config=cargar_config()
    )


def correr(regla: str, inm: Inmueble, ctx: ContextoAntifraude):
    return REGISTRO[regla](inm, ctx)


# precio: mediana 400/m2
def test_precio_muy_bajo(ctx):
    assert isinstance(correr("precio_muy_bajo", anuncio(precio_mxn=8000), ctx), Senal)  # 160/m2 = 40%
    assert correr("precio_muy_bajo", anuncio(precio_mxn=20000), ctx) is None
    assert isinstance(correr("precio_muy_bajo", anuncio(m2=None), ctx), NoEvaluable)
    assert isinstance(correr("precio_muy_bajo", anuncio(colonia="Otra"), ctx), NoEvaluable)


def test_precio_algo_bajo_y_exclusion(ctx):
    inm = anuncio(precio_mxn=12000)  # 240/m2 = 60%
    assert isinstance(correr("precio_algo_bajo", inm, ctx), Senal)
    assert correr("precio_muy_bajo", inm, ctx) is None
    assert correr("precio_algo_bajo", anuncio(precio_mxn=8000), ctx) is None
    assert correr("precio_algo_bajo", anuncio(precio_mxn=20000), ctx) is None
    assert isinstance(correr("precio_algo_bajo", anuncio(m2=None), ctx), NoEvaluable)


def test_deposito_antes_de_visitar(ctx):
    activa = anuncio(descripcion="Para apartar deposita antes de ver el departamento.")
    assert isinstance(correr("deposito_antes_de_visitar", activa, ctx), Senal)
    assert isinstance(
        correr("deposito_antes_de_visitar", anuncio(descripcion="La dirección se da después del depósito."), ctx), Senal
    )
    assert isinstance(correr("deposito_antes_de_visitar", anuncio(descripcion="Aparta con $5,000 hoy."), ctx), Senal)


def test_deposito_de_contrato_no_activa(ctx):
    legitimo = anuncio(descripcion="Renta con un mes de depósito y un mes por adelantado al firmar el contrato.")
    assert correr("deposito_antes_de_visitar", legitimo, ctx) is None
    con_visita = anuncio(descripcion="Puedes visitarlo cuando quieras. Anticipo de un mes al firmar.")
    assert correr("deposito_antes_de_visitar", con_visita, ctx) is None


def test_sin_direccion(ctx):
    assert isinstance(correr("sin_direccion", anuncio(ubicacion_aproximada=True, lat=None, lng=None), ctx), Senal)
    assert correr("sin_direccion", anuncio(), ctx) is None
    con_calle = anuncio(ubicacion_aproximada=True, lat=None, lng=None, descripcion="En calle Durango no. 45.")
    assert correr("sin_direccion", con_calle, ctx) is None


def test_solo_whatsapp(ctx):
    assert isinstance(correr("solo_whatsapp", anuncio(descripcion="Contacto solo por WhatsApp."), ctx), Senal)
    assert correr("solo_whatsapp", anuncio(descripcion="Escríbeme por WhatsApp o llama."), ctx) is None
    con_correo = anuncio(descripcion="Solo por WhatsApp o a casero@correo.com")
    assert correr("solo_whatsapp", con_correo, ctx) is None


def test_whatsapp_extranjero(ctx):
    s = correr("whatsapp_extranjero", anuncio(descripcion="WhatsApp +44 7700 900123."), ctx)
    assert isinstance(s, Senal)
    assert "900123" not in s.evidencia  # el número se oculta
    assert correr("whatsapp_extranjero", anuncio(descripcion="WhatsApp +52 55 1234 5678."), ctx) is None
    assert correr("whatsapp_extranjero", anuncio(descripcion="Sin teléfono."), ctx) is None


def test_ocultar_telefono():
    assert ocultar_telefono("+44 7700 900123") == "+44 7700 90****"


def test_urgencia_presion(ctx):
    assert isinstance(correr("urgencia_presion", anuncio(descripcion="¡Última oportunidad, hoy mismo!"), ctx), Senal)
    assert correr("urgencia_presion", anuncio(), ctx) is None


def test_sin_fotos_ni_visita(ctx):
    assert isinstance(correr("sin_fotos_ni_visita", anuncio(descripcion="Sin fotos por ahora."), ctx), Senal)
    assert correr("sin_fotos_ni_visita", anuncio(), ctx) is None


def test_sin_url_origen(ctx):
    assert isinstance(correr("sin_url_origen", anuncio(fuente="captura_manual"), ctx), Senal)
    assert correr("sin_url_origen", anuncio(fuente="captura_manual", url_origen="https://ejemplo.mx/a"), ctx) is None
    assert correr("sin_url_origen", anuncio(fuente="sintetico"), ctx) is None


def test_m2_inconsistente(ctx):
    assert isinstance(correr("m2_inconsistente", anuncio(m2=100.0, descripcion="Depa de 50 m2."), ctx), Senal)
    assert correr("m2_inconsistente", anuncio(m2=50.0, descripcion="Depa de 50 m2."), ctx) is None
    assert isinstance(correr("m2_inconsistente", anuncio(m2=50.0), ctx), NoEvaluable)


def test_descripcion_duplicada():
    texto = "Departamento amplio y luminoso con balcón cerca del metro y comercios, listo para mudarse hoy."
    idx = IndiceDuplicados()
    idx.agregar("otro", "Juárez", 20000, texto)
    ctx = ContextoAntifraude(indice_duplicados=idx, config=cargar_config())
    assert isinstance(correr("descripcion_duplicada", anuncio(descripcion=texto), ctx), Senal)
    # misma colonia y precio parecido: no cuenta
    idx2 = IndiceDuplicados()
    idx2.agregar("otro", "Roma Norte", 20500, texto)
    ctx2 = ContextoAntifraude(indice_duplicados=idx2, config=cargar_config())
    assert correr("descripcion_duplicada", anuncio(descripcion=texto), ctx2) is None
    assert correr("descripcion_duplicada", anuncio(descripcion="Texto totalmente distinto sobre otra cosa, sin relación alguna aquí."), ctx) is None
