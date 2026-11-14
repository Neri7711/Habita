import { describe, expect, it, vi } from "vitest";
import { ErrorApi, MENSAJE_ERROR_GENERICO } from "./ErrorApi";
import { HttpHabitaClient } from "./HttpHabitaClient";

function respuesta(cuerpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(cuerpo), { status, headers: { "Content-Type": "application/json" } });
}

const perfil = { operacion: "renta", presupuesto_max_mxn: 20000, destino_trabajo: "reforma", mascotas: false } as const;

describe("HttpHabitaClient", () => {
  it("usa /api y marca origen api en stats", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ colonias: 13, anuncios: 300, porcentajeExplicado: 100 }));
    const s = await new HttpHabitaClient({ fetchImpl }).obtenerStats();
    expect(fetchImpl.mock.calls[0][0]).toBe("/api/stats");
    expect(s.origen).toBe("api");
  });

  it("colonias descarta hipotesis_presion y rol", async () => {
    const fila = { colonia: "Roma Norte", alcaldia: "Cuauhtémoc", hipotesis_presion: "alta", rol: "zona_presionada", presion_gentrificacion: 0.8 };
    const fetchImpl = vi.fn().mockResolvedValue(respuesta([fila]));
    const [c] = await new HttpHabitaClient({ fetchImpl }).listarColonias();
    expect(c).toEqual({ colonia: "Roma Norte", alcaldia: "Cuauhtémoc", presion_gentrificacion: 0.8 });
  });

  it("ejemplo ignora el campo extra supuestos", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ titulo: "Estudio", supuestos: ["x"] }));
    const e = await new HttpHabitaClient({ fetchImpl }).obtenerEjemplo();
    expect(e).not.toHaveProperty("supuestos");
    expect(e.titulo).toBe("Estudio");
  });

  it("buscar manda POST con el perfil y rellena listas faltantes", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ opciones: [] }));
    const r = await new HttpHabitaClient({ fetchImpl }).buscarOpciones(perfil);
    const [url, init] = fetchImpl.mock.calls[0];
    expect(url).toBe("/api/buscar");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual(perfil);
    expect(r).toMatchObject({ opciones: [], avisos: [], fuentes: [], supuestos: [] });
  });

  it("un 400 rechaza con el {error} del back y su estado", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ error: "presupuesto_max_mxn debe estar entre 1,000 y 50,000,000" }, 400));
    const err = await new HttpHabitaClient({ fetchImpl }).buscarOpciones(perfil).catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toContain("presupuesto_max_mxn");
    expect(err.estado).toBe(400);
  });

  it("un 500 rechaza con el mensaje genérico", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response("Internal Server Error", { status: 500 }));
    const err = await new HttpHabitaClient({ fetchImpl }).listarZonas().catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toBe(MENSAJE_ERROR_GENERICO);
    expect(err.estado).toBe(500);
  });

  it("red caída rechaza con el mensaje genérico", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    const err = await new HttpHabitaClient({ fetchImpl }).listarColonias().catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toBe(MENSAJE_ERROR_GENERICO);
    expect(err.estado).toBeUndefined();
  });

  it("tiempo agotado rechaza con su propio mensaje", async () => {
    // fetch que nunca responde salvo que lo aborten
    const fetchImpl = vi.fn((_url: string, init?: RequestInit) =>
      new Promise<Response>((_res, rej) => init?.signal?.addEventListener("abort", () => rej(new DOMException("abort", "AbortError")))),
    );
    const err = await new HttpHabitaClient({ fetchImpl: fetchImpl as typeof fetch, timeoutMs: 10 }).obtenerStats().catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toMatch(/tardó demasiado/);
  });

  it("FAQ es local y no llama al back", async () => {
    const fetchImpl = vi.fn();
    const faq = await new HttpHabitaClient({ fetchImpl }).listarFaq();
    expect(faq.length).toBeGreaterThan(0);
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});
