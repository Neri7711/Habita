import type { PerfilRapido, RecomendacionEjemplo, ResultadoBusqueda } from "../domain";
import { nombreZona } from "../domain";
import { MENSAJE_SIN_RESULTADOS } from "./guion";

const AVISOS_EJEMPLO = ["Datos de ejemplo (sintéticos): no son ofertas reales."];
const FUENTES_EJEMPLO = [{ descripcion: "Catálogo de ejemplo de Habita (sintético)", fecha_dato: "" }];

/** Mismos supuestos que completa el back (api_web.py) cuando el perfil rápido no los pregunta. */
function supuestosDe(perfil: PerfilRapido): string[] {
  const supuestos = [
    `Destino de trabajo: ${nombreZona(perfil.destino_trabajo)}.`,
    "Te mueves en transporte público y aceptas hasta 45 minutos de traslado.",
    "Prioridades: precio, luego traslado, luego comunidad.",
  ];
  if (perfil.operacion === "compra") supuestos.push("Enganche del 20% del presupuesto.");
  return supuestos;
}

/** Filtra por operación y presupuesto. No usa mascotas ni destino_trabajo (no hay datos para ello). */
export function buscarOpciones(
  perfil: PerfilRapido,
  catalogo: RecomendacionEjemplo[],
): ResultadoBusqueda {
  const operacion = perfil.operacion === "compra" ? "venta" : "renta";
  const candidatas = catalogo
    .filter((r) => r.operacion === operacion && r.precio_mxn <= perfil.presupuesto_max_mxn)
    .sort((a, b) => b.precio_mxn - a.precio_mxn || a.titulo.localeCompare(b.titulo, "es"));
  const comunes = { avisos: AVISOS_EJEMPLO, fuentes: FUENTES_EJEMPLO, supuestos: supuestosDe(perfil) };
  return candidatas.length > 0
    ? { ...comunes, opciones: candidatas.slice(0, 3) }
    : { ...comunes, opciones: [], mensajeSinResultados: MENSAJE_SIN_RESULTADOS };
}
