import type {
  ColoniaResumen,
  PerfilRapido,
  PreguntaFrecuente,
  RecomendacionEjemplo,
  ResultadoBusqueda,
  StatsLanding,
  ZonaTrabajo,
} from "../domain";
import { FAQ } from "../mocks/faq";
import { ErrorApi, MENSAJE_ERROR_GENERICO } from "./ErrorApi";
import type { HabitaClient } from "./HabitaClient";

export interface HttpOpciones {
  base?: string; // "/api" por defecto (Vite lo reenvía a uv run python scripts/servir_api.py)
  timeoutMs?: number; // 15 s por defecto: la primera llamada puede preparar data/processed
  fetchImpl?: typeof fetch; // para pruebas
}

const MENSAJE_TIEMPO = "Habita tardó demasiado en responder. Inténtalo de nuevo en un momento.";

/** Cliente real contra la API HTTP del back (src/arraigo/api_web.py). Toda falla se rechaza con ErrorApi. */
export class HttpHabitaClient implements HabitaClient {
  readonly origen = "api" as const;
  private readonly base: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor({ base = "/api", timeoutMs = 15_000, fetchImpl }: HttpOpciones = {}) {
    this.base = base.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
    this.fetchImpl = fetchImpl ?? ((...args) => fetch(...args));
  }

  private async pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
    const control = new AbortController();
    const reloj = setTimeout(() => control.abort(), this.timeoutMs);
    let resp: Response;
    try {
      resp = await this.fetchImpl(`${this.base}${ruta}`, {
        ...init,
        headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}) },
        signal: control.signal,
      });
    } catch (e) {
      throw new ErrorApi(control.signal.aborted ? MENSAJE_TIEMPO : MENSAJE_ERROR_GENERICO);
    } finally {
      clearTimeout(reloj);
    }

    let cuerpo: unknown = null;
    try {
      cuerpo = await resp.json();
    } catch {
      // cuerpo vacío o no JSON: se maneja abajo
    }
    if (!resp.ok) {
      const mensaje =
        cuerpo && typeof cuerpo === "object" && typeof (cuerpo as { error?: unknown }).error === "string"
          ? (cuerpo as { error: string }).error
          : MENSAJE_ERROR_GENERICO;
      throw new ErrorApi(mensaje, resp.status);
    }
    if (cuerpo === null) throw new ErrorApi(MENSAJE_ERROR_GENERICO, resp.status);
    return cuerpo as T;
  }

  listarZonas(): Promise<ZonaTrabajo[]> {
    return this.pedir("/zonas");
  }

  listarColonias(): Promise<ColoniaResumen[]> {
    return this.pedir("/colonias");
  }

  async obtenerStats(): Promise<StatsLanding> {
    const s = await this.pedir<StatsLanding>("/stats");
    return { ...s, origen: this.origen };
  }

  obtenerEjemplo(): Promise<RecomendacionEjemplo> {
    return this.pedir("/ejemplo");
  }

  /** El back no sirve FAQ: es contenido editorial del front. */
  listarFaq(): Promise<PreguntaFrecuente[]> {
    return Promise.resolve(FAQ);
  }

  async buscarOpciones(perfil: PerfilRapido): Promise<ResultadoBusqueda> {
    const r = await this.pedir<Partial<ResultadoBusqueda>>("/buscar", {
      method: "POST",
      body: JSON.stringify(perfil),
    });
    return {
      ...r,
      opciones: r.opciones ?? [],
      avisos: r.avisos ?? [],
      fuentes: r.fuentes ?? [],
      supuestos: r.supuestos ?? [],
    };
  }
}
