import type { ColoniaResumen } from "../../domain";
import { useCarga, type Carga } from "./useCarga";

export type EstadoColonias = Carga<ColoniaResumen[]>;

export function useColonias(): EstadoColonias {
  return useCarga((client) => client.listarColonias());
}
