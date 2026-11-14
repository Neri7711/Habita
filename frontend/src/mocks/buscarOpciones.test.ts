import { describe, expect, it } from "vitest";
import type { PerfilRapido } from "../domain";
import { buscarOpciones } from "./buscarOpciones";
import { CATALOGO } from "./recomendaciones";

const perfil = (p: Partial<PerfilRapido>): PerfilRapido => ({
  operacion: "renta",
  presupuesto_max_mxn: 20_000,
  destino_trabajo: "Reforma",
  mascotas: false,
  ...p,
});

describe("buscarOpciones", () => {
  it("renta devuelve solo rentas dentro del presupuesto, máximo 3, de mayor a menor precio", () => {
    const { opciones } = buscarOpciones(perfil({ presupuesto_max_mxn: 15_000 }), CATALOGO);
    expect(opciones.length).toBeGreaterThan(0);
    expect(opciones.length).toBeLessThanOrEqual(3);
    expect(opciones.every((o) => o.operacion === "renta" && o.precio_mxn <= 15_000)).toBe(true);
    const precios = opciones.map((o) => o.precio_mxn);
    expect(precios).toEqual([...precios].sort((a, b) => b - a));
  });

  it("compra devuelve solo ventas", () => {
    const { opciones } = buscarOpciones(perfil({ operacion: "compra", presupuesto_max_mxn: 5_000_000 }), CATALOGO);
    expect(opciones.length).toBeGreaterThan(0);
    expect(opciones.every((o) => o.operacion === "venta")).toBe(true);
  });

  it("presupuesto bajo devuelve vacío con mensaje", () => {
    const r = buscarOpciones(perfil({ presupuesto_max_mxn: 1_000 }), CATALOGO);
    expect(r.opciones).toEqual([]);
    expect(r.mensajeSinResultados).toBeTruthy();
  });

  it("el presupuesto exacto cuenta y el resultado es determinista", () => {
    const exacto = CATALOGO.find((o) => o.operacion === "renta")!.precio_mxn;
    const a = buscarOpciones(perfil({ presupuesto_max_mxn: exacto }), CATALOGO);
    expect(a.opciones.some((o) => o.precio_mxn === exacto)).toBe(true);
    expect(buscarOpciones(perfil({ presupuesto_max_mxn: exacto }), CATALOGO)).toEqual(a);
  });
});
