import { describe, expect, it } from "vitest";
import { validarPerfilRapido, type EntradaFormulario } from "./validacion";

const valida: EntradaFormulario = { operacion: "renta", presupuesto: "12500", destino: "Polanco", mascotas: false };
const con = (e: Partial<EntradaFormulario>) => validarPerfilRapido({ ...valida, ...e });

describe("validarPerfilRapido", () => {
  it("acepta una entrada válida", () => {
    expect(validarPerfilRapido(valida)).toEqual({
      ok: true,
      perfil: { operacion: "renta", presupuesto_max_mxn: 12_500, destino_trabajo: "Polanco", mascotas: false },
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

  it("valida el destino tras trim: 1 y 121 caracteres fallan, 2 y 120 pasan", () => {
    expect(con({ destino: "a" }).ok).toBe(false);
    expect(con({ destino: "  a  " }).ok).toBe(false);
    expect(con({ destino: "" }).ok).toBe(false);
    expect(con({ destino: "a".repeat(121) }).ok).toBe(false);
    expect(con({ destino: "ab" }).ok).toBe(true);
    expect(con({ destino: "a".repeat(120) }).ok).toBe(true);
  });

  it("exige mascotas y operación", () => {
    const r = con({ mascotas: null, operacion: "" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(Object.keys(r.errores).sort()).toEqual(["mascotas", "operacion"]);
  });

  it("reporta todos los campos con error a la vez", () => {
    const r = validarPerfilRapido({ operacion: "x", presupuesto: "", destino: "", mascotas: null });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(Object.keys(r.errores)).toHaveLength(4);
  });
});
