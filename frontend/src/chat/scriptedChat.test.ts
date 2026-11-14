import { describe, expect, it } from "vitest";
import type { PerfilRapido } from "../domain";
import { CATALOGO } from "../mocks/recomendaciones";
import { buscarOpciones } from "../mocks/buscarOpciones";
import { avanzar, iniciar, TEMAS, type EstadoChat, type Intencion } from "./scriptedChat";

const perfil: PerfilRapido = { operacion: "renta", presupuesto_max_mxn: 20_000, destino_trabajo: "Reforma", mascotas: false };
const inicial = () => iniciar(perfil, buscarOpciones(perfil, CATALOGO));

describe("scriptedChat", () => {
  it("iniciar con resultados deja el chat en 'resultados' con tarjeta", () => {
    const { estado, mensajes } = inicial();
    expect(estado.fase).toBe("resultados");
    expect(mensajes[0].tarjeta?.esEjemplo).toBe(true);
    expect(mensajes[0].texto).toContain("ejemplo");
  });

  it("iniciar sin resultados se queda en 'inicio' y ofrece reiniciar", () => {
    const { estado, mensajes } = iniciar(perfil, { opciones: [], mensajeSinResultados: "nada" });
    expect(estado.fase).toBe("inicio");
    expect(mensajes[0].sugerencias).toEqual([{ tipo: "reiniciar" }]);
  });

  it("cada tema responde con tarjeta y pasa a 'explicando'", () => {
    for (const tema of TEMAS) {
      const { estado, mensajes } = avanzar(inicial().estado, { tipo: "tema", tema });
      expect(estado.fase).toBe("explicando");
      expect(mensajes.at(-1)?.autor).toBe("agente");
      expect(mensajes.at(-1)?.tarjeta).toBeDefined();
    }
  });

  it("otra_opcion rota el índice y da la vuelta", () => {
    let estado: EstadoChat = inicial().estado;
    const n = estado.fase === "inicio" ? 0 : estado.opciones.length;
    for (let i = 1; i <= n; i++) {
      estado = avanzar(estado, { tipo: "otra_opcion" }).estado;
      if (estado.fase !== "inicio") expect(estado.indice).toBe(i % n);
    }
  });

  it("texto_libre no cambia fase ni índice y responde fuera de guion", () => {
    const antes = inicial().estado;
    const { estado, mensajes } = avanzar(antes, { tipo: "texto_libre", texto: "hola" });
    expect(estado.fase).toBe(antes.fase);
    expect(estado).toMatchObject({ indice: 0 });
    expect(mensajes).toHaveLength(2);
  });

  it("reiniciar vuelve a 'inicio' desde cualquier fase", () => {
    const explicando = avanzar(inicial().estado, { tipo: "tema", tema: "confianza" }).estado;
    for (const e of [inicial().estado, explicando]) {
      expect(avanzar(e, { tipo: "reiniciar" }).estado.fase).toBe("inicio");
    }
  });

  it("desde 'inicio' cualquier intención responde pidiendo el perfil", () => {
    const e: EstadoChat = { fase: "inicio", contador: 0 };
    const intenciones: Intencion[] = [
      { tipo: "tema", tema: "costo_real" },
      { tipo: "otra_opcion" },
      { tipo: "texto_libre", texto: "x" },
    ];
    for (const i of intenciones) {
      const r = avanzar(e, i);
      expect(r.estado.fase).toBe("inicio");
      expect(r.mensajes).toHaveLength(1);
    }
  });

  it("los ids de mensaje son únicos a lo largo de un flujo", () => {
    let paso = inicial();
    const ids = paso.mensajes.map((m) => m.id);
    for (const i of [{ tipo: "tema", tema: "precio_justo" }, { tipo: "otra_opcion" }, { tipo: "texto_libre", texto: "a" }] as Intencion[]) {
      paso = avanzar(paso.estado, i);
      ids.push(...paso.mensajes.map((m) => m.id));
    }
    expect(new Set(ids).size).toBe(ids.length);
  });
});
