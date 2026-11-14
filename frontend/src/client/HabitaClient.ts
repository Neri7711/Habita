import type {
  ColoniaResumen,
  Origen,
  PerfilRapido,
  PreguntaFrecuente,
  RecomendacionEjemplo,
  ResultadoBusqueda,
  StatsLanding,
} from "../domain";

/** Única frontera con el back. Los componentes solo conocen esta interfaz. */
export interface HabitaClient {
  readonly origen: Origen; // la UI muestra "Datos de ejemplo" si es "mock"
  listarColonias(): Promise<ColoniaResumen[]>;
  obtenerStats(): Promise<StatsLanding>;
  obtenerEjemplo(): Promise<RecomendacionEjemplo>;
  listarFaq(): Promise<PreguntaFrecuente[]>;
  buscarOpciones(perfil: PerfilRapido): Promise<ResultadoBusqueda>;
}
