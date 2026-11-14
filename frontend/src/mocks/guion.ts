import type { Tema } from "../chat/scriptedChat";

export const ETIQUETA_TEMA: Record<Tema, string> = {
  precio_justo: "¿Por qué es precio justo?",
  confianza: "¿Qué tan confiable es el anuncio?",
  comunidad: "¿Cómo es la comunidad?",
  gentrificacion: "¿Qué pasa con la gentrificación aquí?",
  costo_real: "¿Cuál es el costo real?",
};

export const GUION: Record<Tema, string> = {
  precio_justo:
    "Comparé el precio con el de otros anuncios de ejemplo de la misma colonia. Este queda dentro del rango esperado. Son datos de ejemplo: con datos reales te mostraría la fuente y la fecha.",
  confianza:
    "No encontré señales de alerta en este anuncio de ejemplo: el precio es coherente y no pide pagos por adelantado. Recuerda que es un anuncio sintético.",
  comunidad:
    "El dato de comunidad de abajo es ficticio y viene rotulado con su fuente. Con datos reales te diría qué hay cerca y de dónde sale la información.",
  gentrificacion:
    "Hoy solo manejo una hipótesis del equipo sobre la presión en la colonia, no un indicador oficial. Cuando tengamos datos reales te mostraré la fuente.",
  costo_real:
    "Además de la renta o el enganche, considera depósito, póliza o aval, mantenimiento y traslado. En esta demo son cifras de ejemplo y no las desgloso.",
};

export const SALUDO =
  "¡Hola! Soy Habita. Cuéntame qué buscas con el formulario y te muestro opciones de ejemplo.";
export const PIDE_PERFIL =
  "Primero necesito conocer tu búsqueda. Llena el formulario y te muestro opciones.";
export const FUERA_DE_GUION =
  "Por ahora solo puedo responder con las sugerencias de abajo. Elige una y te explico.";
export const NOTA_FILTRO =
  "Nota: en esta demo filtro por operación y presupuesto; aún no uso tu lugar de trabajo ni las mascotas. Son datos de ejemplo.";
export const MENSAJE_SIN_RESULTADOS =
  "Con ese presupuesto no tenemos ejemplos. Prueba subirlo un poco.";
