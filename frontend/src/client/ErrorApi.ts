/** Error del cliente con un mensaje en español listo para mostrarse tal cual en la UI. */
export class ErrorApi extends Error {
  readonly estado?: number; // código HTTP si lo hubo; undefined en fallas de red o tiempo agotado

  constructor(mensaje: string, estado?: number) {
    super(mensaje);
    this.name = "ErrorApi";
    this.estado = estado;
  }
}

export const MENSAJE_ERROR_GENERICO = "No pudimos conectar con Habita. Revisa tu conexión e inténtalo de nuevo.";

/** Mensaje amable para cualquier error: el de ErrorApi si lo es; si no, el genérico. */
export function mensajeDeError(error: unknown): string {
  return error instanceof ErrorApi ? error.message : MENSAJE_ERROR_GENERICO;
}
