import type {
  ColoniaResumen,
  PerfilRapido,
  PreguntaFrecuente,
  RecomendacionEjemplo,
  ResultadoBusqueda,
  StatsLanding,
} from "../domain";
import { buscarOpciones } from "../mocks/buscarOpciones";
import { COLONIAS } from "../mocks/colonias";
import { FAQ } from "../mocks/faq";
import { CATALOGO, EJEMPLO } from "../mocks/recomendaciones";
import { ANUNCIOS_PROVISIONAL } from "../mocks/stats";
import type { HabitaClient } from "./HabitaClient";

export interface MockOpciones {
  latenciaMs?: number; // 400 por defecto; 0 en pruebas
  fallar?: boolean; // hace que toda llamada rechace (para probar estados de error)
}

export class MockHabitaClient implements HabitaClient {
  readonly origen = "mock" as const;
  private readonly latenciaMs: number;
  private readonly fallar: boolean;

  constructor({ latenciaMs = 400, fallar = false }: MockOpciones = {}) {
    this.latenciaMs = latenciaMs;
    this.fallar = fallar;
  }

  private responder<T>(valor: () => T): Promise<T> {
    return new Promise((resolve, reject) => {
      const terminar = () => {
        if (this.fallar) reject(new Error("Fallo simulado del cliente mock"));
        else resolve(valor());
      };
      if (this.latenciaMs > 0) setTimeout(terminar, this.latenciaMs);
      else terminar();
    });
  }

  listarColonias(): Promise<ColoniaResumen[]> {
    return this.responder(() => COLONIAS);
  }

  obtenerStats(): Promise<StatsLanding> {
    return this.responder(() => ({
      colonias: COLONIAS.length,
      anuncios: ANUNCIOS_PROVISIONAL,
      porcentajeExplicado: 100,
      origen: this.origen,
    }));
  }

  obtenerEjemplo(): Promise<RecomendacionEjemplo> {
    return this.responder(() => EJEMPLO);
  }

  listarFaq(): Promise<PreguntaFrecuente[]> {
    return this.responder(() => FAQ);
  }

  buscarOpciones(perfil: PerfilRapido): Promise<ResultadoBusqueda> {
    return this.responder(() => buscarOpciones(perfil, CATALOGO));
  }
}
