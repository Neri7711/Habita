import type { Operacion } from "./backend";

export type Origen = "mock" | "api";

export interface ColoniaResumen {
  colonia: string;
  alcaldia: string;
  hipotesis_presion: "alta" | "media" | "baja"; // hipótesis del equipo, NO indicador real
  rol: "zona_presionada" | "en_transicion" | "alternativa";
}

export interface StatsLanding {
  colonias: number;
  anuncios: number;
  porcentajeExplicado: number;
  origen: Origen;
}

export interface PerfilRapido {
  operacion: "renta" | "compra";
  presupuesto_max_mxn: number; // 1_000 – 50_000_000
  destino_trabajo: string;
  mascotas: boolean;
}

export type VarianteChip = "neutro" | "confianza" | "alerta" | "ia";

export interface RecomendacionEjemplo {
  titulo: string;
  colonia: string;
  operacion: Operacion;
  precio_mxn: number;
  chips: { texto: string; variante: VarianteChip }[];
  datoComunidad: { texto: string; fuente: string; fecha_dato: string };
  fuente: "sintetico";
  esEjemplo: true;
}

export interface ResultadoBusqueda {
  opciones: RecomendacionEjemplo[];
  mensajeSinResultados?: string;
}

export interface PreguntaFrecuente {
  id: string;
  pregunta: string;
  respuesta: string;
}
