// Tipos espejo del back. SUPUESTO derivado de .kiro/specs/01-modelo-datos/design.md.
// Si el back cambia los esquemas, solo se edita este archivo.
export type Operacion = "renta" | "venta";
export type Requisito = "aval" | "poliza" | "deposito_extra" | "ninguno";

export interface Inmueble {
  id: string;
  operacion: Operacion;
  precio_mxn: number;
  colonia: string;
  alcaldia: string;
  lat: number | null;
  lng: number | null;
  ubicacion_aproximada: boolean;
  m2: number | null;
  recamaras: number;
  banos: number;
  estacionamiento: number;
  acepta_mascotas: boolean | null;
  amueblado: boolean | null;
  requisitos: Requisito[];
  descripcion: string;
  fuente: string; // "sintetico" | "captura_manual:<portal>"
  fecha_captura: string; // ISO date
  url_origen: string | null;
  es_fraude_prueba: boolean; // no se muestra ni se usa en la UI
}

export interface Dato<T> {
  valor: T | null;
  fuente: string | null;
  fecha_dato: string | null;
}

export interface Perfil {
  operacion_deseada: "renta" | "compra" | "ambas";
  presupuesto_max_mxn: number;
  destino_trabajo: { lat: number; lng: number; direccion: string };
  mascotas: boolean;
}

export interface Colonia {
  nombre: string;
  alcaldia: string;
  centroide: Dato<{ lat: number; lng: number }>;
  precio_m2_renta_mediana: Dato<number>;
  precio_m2_venta_mediana: Dato<number>;
  indice_delitos: Dato<number>;
  indicador_presion_gentrificacion: Dato<number>;
}
