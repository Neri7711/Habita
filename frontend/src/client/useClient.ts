import { createContext, useContext } from "react";
import type { HabitaClient } from "./HabitaClient";

export const ClientContext = createContext<HabitaClient | null>(null);

/** Devuelve el cliente directamente: `useClient().listarColonias()`. */
export function useClient(): HabitaClient {
  const client = useContext(ClientContext);
  if (!client) throw new Error("useClient debe usarse dentro de <ClientProvider>");
  return client;
}
