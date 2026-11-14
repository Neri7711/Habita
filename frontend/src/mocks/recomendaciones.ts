import type { RecomendacionEjemplo } from "../domain";

const comunidad = (texto: string) => ({
  texto,
  fuente: "Dato de ejemplo (sintético)",
  fecha_dato: "2025-01-01",
});

// Ejemplo de la sección 3.6.
export const EJEMPLO: RecomendacionEjemplo = {
  titulo: "Depa de 2 recámaras en Narvarte Poniente",
  colonia: "Narvarte Poniente",
  operacion: "renta",
  precio_mxn: 16_500,
  chips: [
    { texto: "Precio justo ✓", variante: "confianza" },
    { texto: "Confianza alta", variante: "confianza" },
    { texto: "32 min a tu trabajo", variante: "neutro" },
  ],
  datoComunidad: comunidad("Hay un mercado sobre ruedas los jueves a dos cuadras."),
  fuente: "sintetico",
  esEjemplo: true,
};

const base = { fuente: "sintetico", esEjemplo: true } as const;

// Catálogo sintético que usa buscarOpciones.
export const CATALOGO: RecomendacionEjemplo[] = [
  EJEMPLO,
  {
    ...base,
    titulo: "Estudio amueblado en Juárez",
    colonia: "Juárez",
    operacion: "renta",
    precio_mxn: 14_000,
    chips: [
      { texto: "Precio justo ✓", variante: "confianza" },
      { texto: "Pide póliza jurídica", variante: "alerta" },
    ],
    datoComunidad: comunidad("Zona con alta rotación de inquilinos."),
  },
  {
    ...base,
    titulo: "Depa de 1 recámara en Santa María la Ribera",
    colonia: "Santa María la Ribera",
    operacion: "renta",
    precio_mxn: 11_500,
    chips: [
      { texto: "Precio justo ✓", variante: "confianza" },
      { texto: "Acepta mascotas", variante: "neutro" },
    ],
    datoComunidad: comunidad("Kiosco y mercado de la colonia activos entre semana."),
  },
  {
    ...base,
    titulo: "Depa de 2 recámaras en Portales Norte",
    colonia: "Portales Norte",
    operacion: "renta",
    precio_mxn: 9_800,
    chips: [
      { texto: "Confianza media", variante: "neutro" },
      { texto: "Acepta mascotas", variante: "neutro" },
    ],
    datoComunidad: comunidad("Comunidad vecinal con tianguis dominical."),
  },
  {
    ...base,
    titulo: "Depa de 2 recámaras en Del Valle Centro",
    colonia: "Del Valle Centro",
    operacion: "venta",
    precio_mxn: 4_850_000,
    chips: [
      { texto: "Precio justo ✓", variante: "confianza" },
      { texto: "Confianza alta", variante: "confianza" },
    ],
    datoComunidad: comunidad("Escuelas y parques a menos de 10 minutos a pie."),
  },
  {
    ...base,
    titulo: "Casa de 3 recámaras en Lindavista",
    colonia: "Lindavista",
    operacion: "venta",
    precio_mxn: 3_900_000,
    chips: [
      { texto: "Precio justo ✓", variante: "confianza" },
      { texto: "Revisar escrituras", variante: "alerta" },
    ],
    datoComunidad: comunidad("Colonia residencial con vida de barrio."),
  },
  {
    ...base,
    titulo: "Depa de 1 recámara en San Rafael",
    colonia: "San Rafael",
    operacion: "venta",
    precio_mxn: 2_600_000,
    chips: [
      { texto: "Confianza media", variante: "neutro" },
      { texto: "Precio por debajo del mercado", variante: "alerta" },
    ],
    datoComunidad: comunidad("Colonia en transición con obra nueva cerca."),
  },
];
