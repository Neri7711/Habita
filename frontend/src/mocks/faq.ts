import type { PreguntaFrecuente } from "../domain";

export const FAQ: PreguntaFrecuente[] = [
  {
    id: "cobran",
    pregunta: "¿Habita cobra comisión o me vende algo?",
    respuesta:
      "No. Habita solo recomienda. No cobra comisión ni recibe dinero de inmobiliarias o dueños.",
  },
  {
    id: "precio-justo",
    pregunta: "¿Cómo saben si un precio es justo?",
    respuesta:
      "Comparamos el precio por metro cuadrado con la mediana de la colonia y te mostramos la fuente y la fecha del dato.",
  },
  {
    id: "fraudes",
    pregunta: "¿Cómo detectan anuncios engañosos?",
    respuesta:
      "Revisamos señales como precios muy por debajo del mercado, fotos repetidas o pagos por adelantado. Te explicamos cada alerta; la decisión es tuya.",
  },
  {
    id: "datos-ejemplo",
    pregunta: "¿Los anuncios de la demo son reales?",
    respuesta:
      "No. Mientras veas la etiqueta “Datos de ejemplo”, los anuncios y las cifras son sintéticos y sirven para mostrar cómo funciona Habita.",
  },
  {
    id: "colonias",
    pregunta: "¿Qué colonias cubre Habita?",
    respuesta:
      "Empezamos con un grupo piloto de colonias de la CDMX. La lista completa está en la sección de colonias.",
  },
  {
    id: "asesoria",
    pregunta: "¿Es asesoría legal o financiera?",
    respuesta:
      "No. Habita recomienda y explica, pero no sustituye a un abogado, notario o asesor financiero.",
  },
];
