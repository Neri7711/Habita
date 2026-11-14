import type { ColoniaResumen } from "../../domain";

export type GrupoAlcaldia = { alcaldia: string; colonias: ColoniaResumen[] };

const orden = (a: string, b: string) => a.localeCompare(b, "es");

/** Agrupa por alcaldía: grupos con más colonias primero (empate alfabético), colonias en orden alfabético. */
export function agruparPorAlcaldia(colonias: ColoniaResumen[]): GrupoAlcaldia[] {
  const grupos = new Map<string, ColoniaResumen[]>();
  for (const c of colonias) grupos.set(c.alcaldia, [...(grupos.get(c.alcaldia) ?? []), c]);
  return [...grupos]
    .map(([alcaldia, lista]) => ({ alcaldia, colonias: lista.sort((a, b) => orden(a.colonia, b.colonia)) }))
    .sort((a, b) => b.colonias.length - a.colonias.length || orden(a.alcaldia, b.alcaldia));
}
