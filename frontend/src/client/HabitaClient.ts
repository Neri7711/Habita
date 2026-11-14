import type {
  ColoniaResumen,
  Origen,
  PerfilRapido,
  PreguntaFrecuente,
  RecomendacionEjemplo,
  ResultadoBusqueda,
  StatsLanding,
  ZonaTrabajo,
} from "../domain";

/**
 * Única frontera con el back. Los componentes solo conocen esta interfaz.
 * Toda falla se rechaza con ErrorApi (client/ErrorApi.ts) para que la UI muestre su mensaje tal cual.
 */
export interface HabitaClient {
  readonly origen: Origen; // la UI muestra "Datos de ejemplo" si es "mock"
  listarZonas(): Promise<ZonaTrabajo[]>;
  listarColonias(): Promise<ColoniaResumen[]>;
  obtenerStats(): Promise<StatsLanding>;
  obtenerEjemplo(): Promise<RecomendacionEjemplo>;
  listarFaq(): Promise<PreguntaFrecuente[]>;
  buscarOpciones(perfil: PerfilRapido): Promise<ResultadoBusqueda>;
}
