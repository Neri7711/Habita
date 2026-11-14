import type { PerfilRapido, RecomendacionEjemplo, ResultadoBusqueda } from "../domain";
import { MENSAJE_SIN_RESULTADOS } from "./guion";

/** Filtra por operación y presupuesto. No usa mascotas ni destino_trabajo (no hay datos para ello). */
export function buscarOpciones(
  perfil: PerfilRapido,
  catalogo: RecomendacionEjemplo[],
): ResultadoBusqueda {
  const operacion = perfil.operacion === "compra" ? "venta" : "renta";
  const candidatas = catalogo
    .filter((r) => r.operacion === operacion && r.precio_mxn <= perfil.presupuesto_max_mxn)
    .sort((a, b) => b.precio_mxn - a.precio_mxn || a.titulo.localeCompare(b.titulo, "es"));
  return candidatas.length > 0
    ? { opciones: candidatas.slice(0, 3) }
    : { opciones: [], mensajeSinResultados: MENSAJE_SIN_RESULTADOS };
}
