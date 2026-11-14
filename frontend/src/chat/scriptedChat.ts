import type { PerfilRapido, RecomendacionEjemplo, ResultadoBusqueda } from "../domain";
import {
  ETIQUETA_TEMA,
  FUERA_DE_GUION,
  GUION,
  NOTA_FILTRO,
  PIDE_PERFIL,
  SALUDO,
} from "../mocks/guion";

export type Tema = "precio_justo" | "confianza" | "comunidad" | "gentrificacion" | "costo_real";
export const TEMAS: Tema[] = ["precio_justo", "confianza", "comunidad", "gentrificacion", "costo_real"];

export type Intencion =
  | { tipo: "tema"; tema: Tema }
  | { tipo: "otra_opcion" }
  | { tipo: "texto_libre"; texto: string }
  | { tipo: "reiniciar" };

// `contador` genera ids de mensaje deterministas (sin Date.now ni Math.random).
export type EstadoChat =
  | { fase: "inicio"; contador: number }
  | { fase: "resultados"; contador: number; perfil: PerfilRapido; opciones: RecomendacionEjemplo[]; indice: number }
  | {
      fase: "explicando";
      contador: number;
      perfil: PerfilRapido;
      opciones: RecomendacionEjemplo[];
      indice: number;
      tema: Tema;
    };

export interface Mensaje {
  id: string;
  autor: "usuario" | "agente";
  texto: string;
  tarjeta?: RecomendacionEjemplo;
  sugerencias?: Intencion[];
}

export interface Paso {
  estado: EstadoChat;
  mensajes: Mensaje[];
}

type Borrador = Omit<Mensaje, "id">;

/** Asigna ids consecutivos a partir del contador y devuelve el contador nuevo. */
function numerar(contador: number, borradores: Borrador[]): { mensajes: Mensaje[]; contador: number } {
  return {
    mensajes: borradores.map((b, i) => ({ ...b, id: `m${contador + i}` })),
    contador: contador + borradores.length,
  };
}

const usuario = (texto: string): Borrador => ({ autor: "usuario", texto });

function sugerenciasDe(excluir?: Tema): Intencion[] {
  const temas: Intencion[] = TEMAS.filter((t) => t !== excluir).map((tema) => ({ tipo: "tema", tema }));
  return [...temas, { tipo: "otra_opcion" }, { tipo: "reiniciar" }];
}

export function etiquetaIntencion(i: Intencion): string {
  switch (i.tipo) {
    case "tema":
      return ETIQUETA_TEMA[i.tema];
    case "otra_opcion":
      return "Muéstrame otra opción";
    case "reiniciar":
      return "Cambiar mi búsqueda";
    case "texto_libre":
      return i.texto;
  }
}

export function iniciar(perfil: PerfilRapido, resultado: ResultadoBusqueda): Paso {
  if (resultado.opciones.length === 0) {
    const { mensajes, contador } = numerar(0, [
      {
        autor: "agente",
        texto: resultado.mensajeSinResultados ?? "No encontré opciones de ejemplo para esa búsqueda.",
        sugerencias: [{ tipo: "reiniciar" }],
      },
    ]);
    return { estado: { fase: "inicio", contador }, mensajes };
  }
  // `explicacion` solo la manda la API real, que sí usa trabajo y mascotas; el mock filtra solo operación y presupuesto.
  const deApi = resultado.explicacion !== undefined;
  const nota = deApi
    ? resultado.opciones[0].esEjemplo ? "Son anuncios de ejemplo (sintéticos), no inmuebles reales." : ""
    : NOTA_FILTRO;
  const deEjemplo = deApi ? "" : " de ejemplo";
  const { mensajes, contador } = numerar(0, [
    {
      autor: "agente",
      texto: (
        resultado.opciones.length === 1
          ? `Encontré 1 opción${deEjemplo} para ti. ${nota}`
          : `Encontré ${resultado.opciones.length} opciones${deEjemplo} para ti. Esta es la primera. ${nota}`
      ).trim(),
      tarjeta: resultado.opciones[0],
      sugerencias: sugerenciasDe(),
    },
  ]);
  return {
    estado: { fase: "resultados", contador, perfil, opciones: resultado.opciones, indice: 0 },
    mensajes,
  };
}

export function avanzar(estado: EstadoChat, intencion: Intencion): Paso {
  if (intencion.tipo === "reiniciar") {
    const { mensajes, contador } = numerar(estado.contador, [{ autor: "agente", texto: SALUDO }]);
    return { estado: { fase: "inicio", contador }, mensajes };
  }

  if (estado.fase === "inicio") {
    const { mensajes, contador } = numerar(estado.contador, [{ autor: "agente", texto: PIDE_PERFIL }]);
    return { estado: { ...estado, contador }, mensajes };
  }

  switch (intencion.tipo) {
    case "tema": {
      const opcion = estado.opciones[estado.indice];
      const { mensajes, contador } = numerar(estado.contador, [
        usuario(ETIQUETA_TEMA[intencion.tema]),
        {
          autor: "agente",
          texto: GUION[intencion.tema],
          tarjeta: opcion,
          sugerencias: sugerenciasDe(intencion.tema),
        },
      ]);
      return { estado: { ...estado, fase: "explicando", tema: intencion.tema, contador }, mensajes };
    }
    case "otra_opcion": {
      const indice = (estado.indice + 1) % estado.opciones.length;
      const { mensajes, contador } = numerar(estado.contador, [
        usuario(etiquetaIntencion(intencion)),
        {
          autor: "agente",
          texto: "Va otra opción de ejemplo.",
          tarjeta: estado.opciones[indice],
          sugerencias: sugerenciasDe(),
        },
      ]);
      return {
        estado: { fase: "resultados", contador, perfil: estado.perfil, opciones: estado.opciones, indice },
        mensajes,
      };
    }
    case "texto_libre": {
      const { mensajes, contador } = numerar(estado.contador, [
        usuario(intencion.texto),
        {
          autor: "agente",
          texto: FUERA_DE_GUION,
          sugerencias: sugerenciasDe(estado.fase === "explicando" ? estado.tema : undefined),
        },
      ]);
      return { estado: { ...estado, contador }, mensajes };
    }
  }
}
