import { useCallback, useEffect, useState } from "react";
import { mensajeDeError } from "../../client/ErrorApi";
import { useClient } from "../../client/useClient";
import type { ZonaTrabajo } from "../../domain";

export type EstadoZonas =
  | { fase: "cargando" }
  | { fase: "error"; mensaje: string }
  | { fase: "listo"; zonas: ZonaTrabajo[] };

/** Zonas de trabajo desde el cliente (mock o API), con reintento. */
export function useZonas(): { estado: EstadoZonas; reintentar: () => void } {
  const client = useClient();
  const [estado, setEstado] = useState<EstadoZonas>({ fase: "cargando" });
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let vigente = true;
    setEstado({ fase: "cargando" });
    client.listarZonas().then(
      (zonas) => vigente && setEstado({ fase: "listo", zonas }),
      (error: unknown) => vigente && setEstado({ fase: "error", mensaje: mensajeDeError(error) }),
    );
    return () => {
      vigente = false;
    };
  }, [client, intento]);

  const reintentar = useCallback(() => setIntento((n) => n + 1), []);
  return { estado, reintentar };
}
