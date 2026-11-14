"""Agente (spec 05): lógica de las herramientas MCP, probada sin MCP.

`mcp_server.py` solo traduce argumentos y llama a `arraigo.agente.herramientas`.
"""
from arraigo.agente.contexto import ContextoAgente, ErrorDatos, cargar_contexto, construir_contexto_agente
from arraigo.agente.envoltorio import Envoltorio, Fuente

__all__ = ["ContextoAgente", "ErrorDatos", "Envoltorio", "Fuente", "cargar_contexto", "construir_contexto_agente"]
