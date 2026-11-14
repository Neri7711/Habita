"""Servidor MCP probado en proceso con el cliente en memoria del SDK (sin stdio, sin red, con timeout)."""
import asyncio
import json
from datetime import date

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from arraigo.agente import herramientas as h
from arraigo.agente import mcp_server as srv
from arraigo.agente.contexto import ErrorDatos, construir_contexto_agente
from arraigo.antifraude import ConfigReglas
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble

TIMEOUT_S = 20
HOY = date(2026, 1, 1)
PERFIL = {"operacion_deseada": "renta", "presupuesto_max_mxn": 20000, "ingreso_mensual_mxn": 40000,
          "destino_trabajo": {"lat": 19.43, "lng": -99.19}, "modo_transporte": "transporte_publico",
          "tiempo_max_traslado_min": 40, "prioridades": ["precio", "seguridad"]}


def _dato(v):
    return {"valor": v, "fuente": "dato de prueba", "fecha_dato": HOY}


@pytest.fixture(autouse=True)
def ctx(monkeypatch):
    monkeypatch.setattr(h, "_funcion_calculos", lambda nombre: None)  # sin spec 03: respuestas "pendiente"
    colonias = [
        Colonia.model_validate({"nombre": "Roma Norte", "alcaldia": "Cuauhtémoc",
                                "indicador_presion_gentrificacion": _dato(0.8), "indice_delitos": _dato(50)}),
        Colonia.model_validate({"nombre": "Narvarte Poniente", "alcaldia": "Benito Juárez",
                                "indicador_presion_gentrificacion": _dato(0.4), "indice_delitos": _dato(20)}),
    ]
    base = dict(alcaldia="X", lat=19.4, lng=-99.16, m2=50.0, recamaras=1, banos=1, fuente="sintetico",
                fecha_captura=HOY, operacion="renta")
    inmuebles = [Inmueble(id="r1", colonia="Roma Norte", precio_mxn=15000, **base),
                 Inmueble(id="r2", colonia="Narvarte Poniente", precio_mxn=12000, es_fraude_prueba=True, **base)]
    contexto = construir_contexto_agente(inmuebles, colonias, ConfigReglas(version=1, reglas={}), HOY)
    srv.configurar_contexto(contexto)
    yield contexto
    srv.configurar_contexto(None)


def correr(coro):
    return asyncio.run(asyncio.wait_for(coro, TIMEOUT_S))


async def _con_cliente(accion):
    async with create_connected_server_and_client_session(srv.mcp) as cliente:
        return await accion(cliente)


def _datos(resultado) -> dict:
    assert not resultado.isError, resultado.content
    if resultado.structuredContent is not None:
        return resultado.structuredContent
    return json.loads(resultado.content[0].text)


LLAMADAS = {
    "buscar_inmuebles": {"perfil": PERFIL, "limite": 3},
    "costo_real": {"inmueble_id": "r1", "perfil": PERFIL},
    "precio_justo": {"inmueble_id": "r1"},
    "score_fraude": {"inmueble_id": "r2"},
    "info_colonia": {"colonia": "roma norte"},
    "alternativas_equilibradas": {"perfil": PERFIL, "colonia_origen": "Roma Norte"},
}


def test_lista_seis_herramientas_de_solo_lectura():
    async def accion(cliente):
        return await cliente.list_tools()

    herramientas = correr(_con_cliente(accion)).tools
    assert sorted(t.name for t in herramientas) == sorted(srv.HERRAMIENTAS)
    for t in herramientas:
        assert t.annotations and t.annotations.readOnlyHint is True
        assert t.description and len(t.description) > 40
    buscar = next(t for t in herramientas if t.name == "buscar_inmuebles")
    perfil = buscar.inputSchema["properties"]["perfil"]
    assert "prioridades" in perfil["properties"] and "$ref" not in json.dumps(perfil)


def test_instructions_no_vacias():
    # Son las que el servidor envía al cliente en la respuesta de `initialize`.
    opciones = srv.mcp._mcp_server.create_initialization_options()
    assert opciones.instructions and "señales de riesgo" in opciones.instructions
    assert "No contactas caseros" in opciones.instructions


def test_llama_cada_herramienta_por_el_cliente():
    async def accion(cliente):
        return {n: await cliente.call_tool(n, args) for n, args in LLAMADAS.items()}

    salidas = {n: _datos(r) for n, r in correr(_con_cliente(accion)).items()}
    assert [r["inmueble"]["id"] for r in salidas["buscar_inmuebles"]["datos"]["resultados"]] == ["r2", "r1"]
    assert salidas["buscar_inmuebles"]["datos"]["excluidos_por_riesgo"] == 0
    assert salidas["costo_real"]["datos"] == {"aviso": "pendiente spec 03"}
    assert salidas["precio_justo"]["datos"] == {"aviso": "pendiente spec 03"}
    assert salidas["info_colonia"]["datos"]["nombre"] == "Roma Norte"
    assert [a["colonia"] for a in salidas["alternativas_equilibradas"]["datos"]["alternativas"]] == ["Narvarte Poniente"]
    texto = json.dumps(salidas, ensure_ascii=False).lower()
    assert "es_fraude_prueba" not in texto and "estafa" not in texto
    assert all(s["ok"] for s in salidas.values())


def test_entrada_invalida_devuelve_envoltorio_en_espanol():
    async def accion(cliente):
        return await cliente.call_tool("buscar_inmuebles", {"perfil": {**PERFIL, "prioridades": ["precio", "precio"]}})

    datos = _datos(correr(_con_cliente(accion)))
    assert datos["ok"] is False and "prioridades: no puede tener repetidos" in datos["error"]


def test_sin_datos_responde_error_con_comando(monkeypatch):
    srv.configurar_contexto(None)
    monkeypatch.setattr(srv, "cargar_contexto", lambda: (_ for _ in ()).throw(
        ErrorDatos("Falta el archivo inmuebles.json. Genéralo con: uv run python scripts/cargar_dataset.py")))

    async def accion(cliente):
        return await cliente.call_tool("info_colonia", {"colonia": "Roma Norte"})

    datos = _datos(correr(_con_cliente(accion)))
    assert datos["ok"] is False and "scripts/cargar_dataset.py" in datos["error"]


def test_excepcion_inesperada_no_sale_al_cliente(monkeypatch):
    def explota(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(h, "score_fraude", explota)
    datos = correr(srv.mcp.call_tool("score_fraude", {"inmueble_id": "r1"}))
    # call_tool en proceso devuelve (contenido, estructurado) o el contenido; buscamos el envoltorio.
    estructurado = datos[1] if isinstance(datos, tuple) else json.loads(datos[0].text)
    assert estructurado["ok"] is False and "Error interno" in estructurado["error"]
