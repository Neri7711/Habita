import type { PerfilRapido } from "./ui";

export const PRESUPUESTO_MIN = 1_000;
export const PRESUPUESTO_MAX = 50_000_000;

export interface EntradaFormulario {
  operacion: string;
  presupuesto: string;
  destino: string; // id de ZonaTrabajo elegido en el <select>; "" si no eligió
  mascotas: boolean | null;
}

export type CampoFormulario = "operacion" | "presupuesto" | "destino" | "mascotas";
export type ResultadoValidacion =
  | { ok: true; perfil: PerfilRapido }
  | { ok: false; errores: Partial<Record<CampoFormulario, string>> };

/** Acepta "12,500", "$12 500" y "12500". Devuelve null si no es un entero. */
export function parsearPresupuesto(texto: string): number | null {
  const limpio = texto.replace(/[$,\s]/g, "");
  return /^\d+$/.test(limpio) ? Number(limpio) : null;
}

/** `idsZonas`: ids válidos de la lista que regresó `listarZonas()`; el destino debe ser uno de ellos. */
export function validarPerfilRapido(entrada: EntradaFormulario, idsZonas: readonly string[]): ResultadoValidacion {
  const errores: Partial<Record<CampoFormulario, string>> = {};

  if (entrada.operacion !== "renta" && entrada.operacion !== "compra") {
    errores.operacion = "Elige si quieres rentar o comprar.";
  }

  const presupuesto = parsearPresupuesto(entrada.presupuesto);
  if (presupuesto === null) {
    errores.presupuesto = "Escribe tu presupuesto máximo en pesos, solo números.";
  } else if (presupuesto < PRESUPUESTO_MIN || presupuesto > PRESUPUESTO_MAX) {
    errores.presupuesto = "El presupuesto debe estar entre $1,000 y $50,000,000.";
  }

  if (entrada.destino === "") {
    errores.destino = "Elige la zona donde trabajas.";
  } else if (!idsZonas.includes(entrada.destino)) {
    errores.destino = "Elige una zona de la lista.";
  }

  if (typeof entrada.mascotas !== "boolean") {
    errores.mascotas = "Indica si tienes mascotas.";
  }

  if (Object.keys(errores).length > 0) return { ok: false, errores };
  return {
    ok: true,
    perfil: {
      operacion: entrada.operacion as PerfilRapido["operacion"],
      presupuesto_max_mxn: presupuesto as number,
      destino_trabajo: entrada.destino,
      mascotas: entrada.mascotas as boolean,
    },
  };
}
