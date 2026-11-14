import { useEffect, useRef, useState } from "react";
import { mensajeDeError } from "../../client/ErrorApi";
import type { HabitaClient } from "../../client/HabitaClient";
import { useClient } from "../../client/useClient";

export type Carga<T> =
  | { tipo: "cargando" }
  | { tipo: "error"; mensaje: string; reintentar: () => void }
  | { tipo: "listo"; datos: T };

/** Pide un dato al cliente y expone tres estados claros; `reintentar` repite la misma petición. */
export function useCarga<T>(pedir: (client: HabitaClient) => Promise<T>): Carga<T> {
  const client = useClient();
  const [intento, setIntento] = useState(0);
  const [estado, setEstado] = useState<Carga<T>>({ tipo: "cargando" });
  const pedirRef = useRef(pedir);
  pedirRef.current = pedir;

  useEffect(() => {
    let vivo = true;
    setEstado({ tipo: "cargando" });
    pedirRef.current(client).then(
      (datos) => vivo && setEstado({ tipo: "listo", datos }),
      (error) =>
        vivo &&
        setEstado({ tipo: "error", mensaje: mensajeDeError(error), reintentar: () => setIntento((n) => n + 1) }),
    );
    return () => {
      vivo = false;
    };
  }, [client, intento]);

  return estado;
}
