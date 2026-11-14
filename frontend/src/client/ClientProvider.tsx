import { useState, type ReactNode } from "react";
import type { HabitaClient } from "./HabitaClient";
import { MockHabitaClient } from "./MockHabitaClient";
import { ClientContext } from "./useClient";

function crearClienteDesdeEntorno(): HabitaClient {
  const tipo = import.meta.env.VITE_HABITA_CLIENT ?? "mock";
  if (tipo === "api") {
    throw new Error("VITE_HABITA_CLIENT=api: HttpHabitaClient aún no existe (pendiente del back).");
  }
  return new MockHabitaClient({ fallar: import.meta.env.VITE_MOCK_FAIL === "1" });
}

export function ClientProvider({ client, children }: { client?: HabitaClient; children: ReactNode }) {
  const [valor] = useState<HabitaClient>(() => client ?? crearClienteDesdeEntorno());
  return <ClientContext.Provider value={valor}>{children}</ClientContext.Provider>;
}
