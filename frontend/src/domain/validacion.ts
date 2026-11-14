import type { PerfilRapido } from "./ui";

export const PRESUPUESTO_MIN = 1_000;
export const PRESUPUESTO_MAX = 50_000_000;

export interface EntradaFormulario {
  operacion: string;
  presupuesto: string;
  destino: string;
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

export function validarPerfilRapido(entrada: EntradaFormulario): ResultadoValidacion {
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

  const destino = entrada.destino.trim();
  if (destino.length < 2 || destino.length > 120) {
    errores.destino = "Cuéntanos dónde trabajas (entre 2 y 120 caracteres).";
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
      destino_trabajo: destino,
      mascotas: entrada.mascotas as boolean,
    },
  };
}
