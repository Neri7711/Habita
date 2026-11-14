import { describe, expect, it, vi } from "vitest";
import { ErrorApi, MENSAJE_ERROR_GENERICO } from "./ErrorApi";
import { HttpHabitaClient } from "./HttpHabitaClient";

function respuesta(cuerpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(cuerpo), { status, headers: { "Content-Type": "application/json" } });
}

describe("HttpHabitaClient", () => {
  it("usa /api y marca origen api en stats", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ colonias: 13, anuncios: 300, porcentajeExplicado: 100 }));
    const c = new HttpHabitaClient({ fetchImpl });
    const s = await c.obtenerStats();
    expect(fetchImpl.mock.calls[0][0]).toBe("/api/stats");
    expect(s.origen).toBe("api");
  });

  it("buscar manda POST con el perfil y rellena listas faltantes", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ opciones: [] }));
    const c = new HttpHabitaClient({ fetchImpl });
    const perfil = { operacion: "renta", presupuesto_max_mxn: 20000, destino_trabajo: "reforma", mascotas: false } as const;
    const r = await c.buscarOpciones(perfil);
    const [url, init] = fetchImpl.mock.calls[0];
    expect(url).toBe("/api/buscar");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual(perfil);
    expect(r).toMatchObject({ opciones: [], avisos: [], fuentes: [], supuestos: [] });
  });

  it("un 400 rechaza con el mensaje del back y su estado", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(respuesta({ error: "presupuesto fuera de rango" }, 400));
    const err = await new HttpHabitaClient({ fetchImpl }).listarZonas().catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toBe("presupuesto fuera de rango");
    expect(err.estado).toBe(400);
  });

  it("una falla de red rechaza con el mensaje genérico", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    const err = await new HttpHabitaClient({ fetchImpl }).listarColonias().catch((e) => e);
    expect(err).toBeInstanceOf(ErrorApi);
    expect(err.message).toBe(MENSAJE_ERROR_GENERICO);
  });

  it("FAQ es local y no llama al back", async () => {
    const fetchImpl = vi.fn();
    const faq = await new HttpHabitaClient({ fetchImpl }).listarFaq();
    expect(faq.length).toBeGreaterThan(0);
    expect(fetchImpl).not.toHaveBeenCalled();
  });
});
