"""HTTP mínimo con caché en disco (sin dependencias extra)."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "arraigo-hackathon/0.1"
CACHE_DIR = Path(__file__).resolve().parents[3] / ".cache" / "http"
_ultima_llamada: dict[str, float] = {}


def get_json(
    url: str,
    params: dict | None = None,
    *,
    data: dict | None = None,
    min_intervalo_s: float = 0.0,
    timeout: int = 60,
    usar_cache: bool = True,
):
    """GET (o POST de formulario si se pasa `data`) que regresa JSON, con caché y límite de ritmo por host."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    cuerpo = urllib.parse.urlencode(data).encode() if data else None
    clave = hashlib.sha256(url.encode() + (cuerpo or b"")).hexdigest()
    ruta = CACHE_DIR / f"{clave}.json"
    if usar_cache and ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))

    host = urllib.parse.urlparse(url).netloc
    espera = min_intervalo_s - (time.monotonic() - _ultima_llamada.get(host, 0))
    if espera > 0:
        time.sleep(espera)
    req = urllib.request.Request(url, data=cuerpo, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resultado = json.loads(resp.read().decode("utf-8"))
    _ultima_llamada[host] = time.monotonic()

    if usar_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    return resultado


def descargar(url: str, destino: Path) -> Path:
    """Descarga un archivo a `destino` si todavía no existe."""
    if destino.exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(destino, "wb") as f:
        while bloque := resp.read(1 << 20):
            f.write(bloque)
    return destino
