import { useState, type ReactNode } from "react";
import type { HabitaClient } from "./HabitaClient";
import { HttpHabitaClient } from "./HttpHabitaClient";
import { MockHabitaClient } from "./MockHabitaClient";
import { ClientContext } from "./useClient";

/** VITE_HABITA_CLIENT=api usa el back real (VITE_HABITA_API_URL, "/api" por defecto); cualquier otro valor, el mock. */
function crearClienteDesdeEntorno(): HabitaClient {
  const tipo = import.meta.env.VITE_HABITA_CLIENT ?? "mock";
  if (tipo === "api") {
    return new HttpHabitaClient({ base: import.meta.env.VITE_HABITA_API_URL || "/api" });
  }
  return new MockHabitaClient({ fallar: import.meta.env.VITE_MOCK_FAIL === "1" });
}

export function ClientProvider({ client, children }: { client?: HabitaClient; children: ReactNode }) {
  const [valor] = useState<HabitaClient>(() => client ?? crearClienteDesdeEntorno());
  return <ClientContext.Provider value={valor}>{children}</ClientContext.Provider>;
}
