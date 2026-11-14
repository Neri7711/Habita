import type { Operacion } from "./backend";

export type Origen = "mock" | "api";

export interface ColoniaResumen {
  colonia: string;
  alcaldia: string;
  // Hipótesis del equipo, NO indicador real: nunca se muestran en la UI. La API puede no mandarlos.
  hipotesis_presion?: "alta" | "media" | "baja";
  rol?: "zona_presionada" | "en_transicion" | "alternativa";
  presion_gentrificacion?: number | null; // 0–1, calculada por el back (spec 02)
}

/** Zona de trabajo con coordenadas; el formulario elige una de una lista cerrada. */
export interface ZonaTrabajo {
  id: string;
  nombre: string;
  lat: number;
  lng: number;
}

/** Fuente citada por el back. `fecha_dato` puede venir vacía. */
export interface Fuente {
  descripcion: string;
  fecha_dato: string;
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
  destino_trabajo: string; // id de ZonaTrabajo (ver domain/zonas.ts)
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

export type BandaPrecio = "justo" | "caro" | "sospechosamente_barato" | "sin_dato";
export type NivelRiesgo = "bajo" | "medio" | "alto";

export interface CostoRealResumen {
  total_mensual_mxn: number;
  costo_monetario_mxn?: number;
  vivienda_mxn?: number;
  transporte_mxn?: number;
  servicios_mxn?: number;
  tiempo_valorizado_mxn?: number;
  minutos_traslado?: number;
}

/** Opción de búsqueda: la tarjeta de ejemplo más lo que agrega la API (todo opcional para que el mock siga valiendo). */
export interface OpcionBusqueda extends RecomendacionEjemplo {
  id?: string;
  porQue?: string;
  costoReal?: CostoRealResumen;
  precioJusto?: BandaPrecio;
  riesgo?: NivelRiesgo;
  presionGentrificacion?: number | null;
  ubicacionAproximada?: boolean;
  avisos?: string[];
}

export interface ResultadoBusqueda {
  opciones: OpcionBusqueda[];
  mensajeSinResultados?: string;
  explicacion?: string;
  avisos: string[]; // generales de la búsqueda (sintéticos, estimaciones)
  fuentes: Fuente[];
  supuestos: string[]; // lo que el back asume porque el perfil rápido no lo pregunta → "Asumimos que…"
  alternativas?: { explicacion: string };
}

export interface PreguntaFrecuente {
  id: string;
  pregunta: string;
  respuesta: string;
}
