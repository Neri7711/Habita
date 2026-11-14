"""Capa de I/O de la spec 03: geocodificar el destino y obtener la tasa de referencia (R1.6, R1.7, R5.2-R5.4).

La red solo se toca aquí; las funciones de `arraigo.calculos` reciben los resultados como parámetros.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from pydantic import ValidationError

from arraigo.calculos.modelos import TasaReferencia
from arraigo.calculos.supuestos import (
    RUTA_TASA,
    ConfigCalculos,
    cargar_tasa_guardada,
    tasa_respaldo,
)
from arraigo.fuentes import banxico, nominatim
from arraigo.schemas.colonia import Colonia
from arraigo.schemas.inmueble import Inmueble, Operacion
from arraigo.schemas.perfil import Ubicacion


class DireccionNoEncontrada(ValueError):
    """Nominatim no encontró la dirección; hay que pedir una más precisa."""


def geocodificar_destino(direccion: str) -> Ubicacion:
    """Convierte una dirección de texto en coordenadas (Nominatim, 1 solicitud por segundo, con caché)."""
    texto = (direccion or "").strip()
    pedir_mas = DireccionNoEncontrada(
        f"No encontramos la dirección «{texto}». Escríbela con más detalle (calle, número, colonia y alcaldía)."
    )
    if not texto:
        raise pedir_mas
    consulta = texto if "méxico" in texto.lower() or "mexico" in texto.lower() else f"{texto}, Ciudad de México"
    r = nominatim.geocodificar(consulta)
    if r is None:
        raise pedir_mas
    try:
        return Ubicacion(lat=r["lat"], lng=r["lng"], direccion=r.get("nombre") or texto)
    except ValidationError as e:  # fuera de la zona metropolitana
        raise DireccionNoEncontrada(
            f"La dirección «{texto}» quedó fuera de la zona metropolitana de la CDMX. Escríbela con más detalle."
        ) from e


def _parsear_fecha(texto: str) -> date:
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"fecha de Banxico no reconocida: {texto!r}")


def obtener_tasa_referencia(config: ConfigCalculos, ruta: Path = RUTA_TASA) -> TasaReferencia:
    """TIIE a 28 días: Banxico → última tasa guardada → tasa de respaldo de la tabla de supuestos."""
    serie = config.compra.serie_banxico
    try:  # sin BANXICO_TOKEN el cliente lanza RuntimeError
        d = banxico.dato_oportuno(serie)
        tasa = TasaReferencia(
            tasa_pct=float(str(d["dato"]).replace(",", "")),
            fecha=_parsear_fecha(d["fecha"]),
            fuente=f"{banxico.FUENTE}, serie {serie}",
        )
    except Exception:  # sin token, sin red o respuesta inesperada
        try:
            guardada = cargar_tasa_guardada(ruta)
        except (ValueError, OSError):
            guardada = None
        return guardada or tasa_respaldo(config)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(json.loads(tasa.model_dump_json()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return tasa


def completar_medianas(colonias: list[Colonia], inmuebles: list[Inmueble]) -> list[Colonia]:
    """Rellena las medianas por m² que falten con las del antifraude (spec 04), sin recalcularlas aparte.

    `colonias.json` trae medianas vacías hasta que haya anuncios reales; el antifraude usa entonces la
    mediana del propio dataset. Aquí se reutilizan exactamente esos valores (R7.7).
    """
    from arraigo.antifraude import construir_contexto
    from arraigo.antifraude.texto import normalizar

    medianas = construir_contexto(inmuebles, colonias).medianas_m2
    resultado = []
    for c in colonias:
        cambios = {}
        for campo, op in (("precio_m2_renta_mediana", Operacion.renta), ("precio_m2_venta_mediana", Operacion.venta)):
            extra = medianas.get((normalizar(c.nombre), op))
            if getattr(c, campo).valor is None and extra is not None:
                cambios[campo] = extra
        resultado.append(c.model_copy(update=cambios))
    return resultado
