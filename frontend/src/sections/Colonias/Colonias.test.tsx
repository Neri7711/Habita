import type { ColoniaResumen } from "../../domain";
import { agruparPorAlcaldia } from "./agruparPorAlcaldia";

const c = (colonia: string, alcaldia: string): ColoniaResumen => ({
  colonia,
  alcaldia,
  hipotesis_presion: "media",
  rol: "alternativa",
});

describe("agruparPorAlcaldia", () => {
  it("agrupa, ordena grupos por tamaño y colonias alfabéticamente", () => {
    const grupos = agruparPorAlcaldia([
      c("Tacubaya", "Miguel Hidalgo"),
      c("Roma Norte", "Cuauhtémoc"),
      c("Lindavista", "Gustavo A. Madero"),
      c("Juárez", "Cuauhtémoc"),
    ]);
    expect(grupos.map((g) => g.alcaldia)).toEqual(["Cuauhtémoc", "Gustavo A. Madero", "Miguel Hidalgo"]);
    expect(grupos[0].colonias.map((x) => x.colonia)).toEqual(["Juárez", "Roma Norte"]);
  });

  it("devuelve una lista vacía sin colonias", () => {
    expect(agruparPorAlcaldia([])).toEqual([]);
  });
});
