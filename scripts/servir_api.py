"""Levanta la API HTTP para el front. Uso: uv run python scripts/servir_api.py  ->  http://127.0.0.1:8000/api/salud"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("arraigo.api_web:app", host="127.0.0.1", port=8000)
