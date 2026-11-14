import { describe, expect, it } from "vitest";
import { validarPerfilRapido, type EntradaFormulario } from "./validacion";
import { ZONAS_TRABAJO } from "./zonas";

const IDS = ZONAS_TRABAJO.map((z) => z.id);
const valida: EntradaFormulario = { operacion: "renta", presupuesto: "12500", destino: "polanco", mascotas: false };
const con = (e: Partial<EntradaFormulario>) => validarPerfilRapido({ ...valida, ...e }, IDS);

describe("validarPerfilRapido", () => {
  it("acepta una entrada válida y envía el id de la zona", () => {
    expect(validarPerfilRapido(valida, IDS)).toEqual({
      ok: true,
      perfil: { operacion: "renta", presupuesto_max_mxn: 12_500, destino_trabajo: "polanco", mascotas: false },
    });
  });

  it.each([["12,500"], ["$12 500"], ["1000"], ["50000000"]])("acepta presupuesto %s", (presupuesto) => {
    expect(con({ presupuesto }).ok).toBe(true);
  });

  it.each([["0"], ["999"], ["50000001"], [""], ["abc"], ["12.5"], ["-5000"]])("rechaza presupuesto '%s'", (presupuesto) => {
    const r = con({ presupuesto });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errores.presupuesto).toBeTruthy();
  });

  it("el destino es obligatorio", () => {
    const r = con({ destino: "" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errores.destino).toBe("Elige la zona donde trabajas.");
  });

  it("el destino debe ser un id de la lista", () => {
    const r = con({ destino: "Polanco" }); // nombre, no id
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.errores.destino).toBe("Elige una zona de la lista.");
    expect(validarPerfilRapido(valida, []).ok).toBe(false); // sin zonas cargadas no hay destino válido
  });

  it("exige mascotas y operación", () => {
    const r = con({ mascotas: null, operacion: "" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(Object.keys(r.errores).sort()).toEqual(["mascotas", "operacion"]);
  });

  it("reporta todos los campos con error a la vez", () => {
    const r = validarPerfilRapido({ operacion: "x", presupuesto: "", destino: "", mascotas: null }, IDS);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(Object.keys(r.errores)).toHaveLength(4);
  });
});
