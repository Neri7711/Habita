from datetime import date

import pytest

from arraigo.antifraude import ConfigReglas, ContextoAntifraude, evaluar_anuncio, evaluar_anuncio_nuevo
from arraigo.antifraude.duplicados import IndiceDuplicados
from arraigo.antifraude.score import nivel_de_score
from arraigo.schemas.colonia import Dato
from arraigo.schemas.inmueble import Inmueble, Operacion

PROHIBIDAS = ("estafador", "ladron", "ladrón", "seguro")


def config(**pesos) -> ConfigReglas:
    reglas = {"urgencia_presion": {"peso": 10, "frases": ["\\burge\\b"]},
              "sin_fotos_ni_visita": {"peso": 20, "frases": ["\\bsin fotos\\b"]},
              "deposito_antes_de_visitar": {"peso": 35, "frases_directas": ["\\bdespues del deposito\\b"]},
              "precio_muy_bajo": {"peso": 40, "ratio_max": 0.5}}
    for k, v in pesos.items():
        reglas[k]["peso"] = v
    return ConfigReglas(version=1, reglas=reglas)


def anuncio(descripcion="Departamento.", **kw) -> Inmueble:
    base = dict(id="s1", operacion="renta", precio_mxn=20000, colonia="Roma Norte", alcaldia="Cuauhtémoc",
                lat=19.42, lng=-99.16, m2=50.0, recamaras=1, banos=1, descripcion=descripcion,
                fuente="sintetico", fecha_captura=date(2026, 1, 1))
    base.update(kw)
    return Inmueble(**base)


def contexto(cfg: ConfigReglas | None = None) -> ContextoAntifraude:
    med = Dato[float](valor=400.0, fuente="anuncios de prueba", fecha_dato=date(2026, 1, 1))
    return ContextoAntifraude(medianas_m2={("roma norte", Operacion.renta): med},
                              indice_duplicados=IndiceDuplicados(), config=cfg or config())


def test_suma_de_puntos():
    r = evaluar_anuncio(anuncio("Urge. Sin fotos."), contexto())
    assert r.score_riesgo == 30
    assert [s.regla for s in r.senales] == ["sin_fotos_ni_visita", "urgencia_presion"]  # mayor a menor
    assert r.nivel == "medio"


def test_tope_100():
    r = evaluar_anuncio(anuncio("Urge. Sin fotos. Después del depósito.", precio_mxn=5000), contexto())
    assert sum(s.puntos for s in r.senales) == 105
    assert r.score_riesgo == 100
    assert r.nivel == "alto"


@pytest.mark.parametrize("score,nivel", [(0, "bajo"), (29, "bajo"), (30, "medio"), (59, "medio"), (60, "alto"), (100, "alto")])
def test_niveles(score, nivel):
    assert nivel_de_score(score, config()) == nivel


def test_explicaciones_no_vacias_y_sin_palabras_prohibidas():
    r = evaluar_anuncio(anuncio("Urge. Sin fotos. Después del depósito.", precio_mxn=5000), contexto())
    textos = [r.resumen, r.recomendacion] + [s.explicacion for s in r.senales] + [s.evidencia for s in r.senales]
    for s in r.senales:
        assert s.explicacion.strip() and s.evidencia.strip()
    for t in textos:
        assert not any(p in t.lower() for p in PROHIBIDAS), t


def test_sin_senales_no_dice_que_es_seguro():
    r = evaluar_anuncio(anuncio("Departamento."), contexto())
    assert r.score_riesgo == 0 and r.nivel == "bajo" and not r.senales
    assert "no garantiza" in r.resumen
    assert "seguro" not in (r.resumen + r.recomendacion).lower()


def test_sintetico_y_fuente_de_referencia():
    r = evaluar_anuncio(anuncio(), contexto())
    assert r.es_sintetico and "sintético" in r.resumen
    assert r.fuente_referencia and "Roma Norte" in r.fuente_referencia and "2026-01-01" in r.fuente_referencia
    r2 = evaluar_anuncio(anuncio(fuente="captura_manual"), contexto())
    assert not r2.es_sintetico and "sintético" not in r2.resumen


def test_no_evaluables_se_registran_y_no_suman():
    r = evaluar_anuncio(anuncio(colonia="Sin Mediana"), contexto())
    assert r.score_riesgo == 0
    assert any(n.startswith("precio_muy_bajo") for n in r.no_evaluables)
    assert r.fuente_referencia is None


def test_determinista():
    a = anuncio("Urge. Sin fotos.")
    assert evaluar_anuncio(a, contexto()) == evaluar_anuncio(a, contexto())


def test_anuncio_nuevo():
    r = evaluar_anuncio_nuevo("Urge. Sin fotos.", 20000, "Roma Norte", contexto(), m2=50)
    assert r.score_riesgo == 30 and r.id == "nuevo"


def _contexto_desde_dataset(fuente: str, n: int = 5):
    from arraigo.antifraude.score import construir_contexto

    anuncios = [anuncio(id=f"m{k}", fuente=fuente, precio_mxn=20000 + k * 100) for k in range(n)]
    return construir_contexto(anuncios, [], config())


def test_mediana_de_sinteticos_se_etiqueta_como_sintetica():
    dato = _contexto_desde_dataset("sintetico").medianas_m2[("roma norte", Operacion.renta)]
    assert "sint" in dato.fuente.lower()  # banda_precio.py depende de esto para avisar al usuario
    assert "capturados" not in dato.fuente


def test_mediana_de_reales_se_etiqueta_como_capturada():
    dato = _contexto_desde_dataset("captura_manual:portal").medianas_m2[("roma norte", Operacion.renta)]
    assert dato.fuente == "mediana de anuncios capturados (n=5)"
