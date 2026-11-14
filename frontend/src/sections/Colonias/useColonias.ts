import { useEffect, useState } from "react";
import { useClient } from "../../client/useClient";
import type { ColoniaResumen } from "../../domain";

export type EstadoColonias = "cargando" | "error" | ColoniaResumen[];

export function useColonias(): EstadoColonias {
  const client = useClient();
  const [estado, setEstado] = useState<EstadoColonias>("cargando");

  useEffect(() => {
    let vivo = true;
    client
      .listarColonias()
      .then((colonias) => vivo && setEstado(colonias))
      .catch(() => vivo && setEstado("error"));
    return () => {
      vivo = false;
    };
  }, [client]);

  return estado;
}
