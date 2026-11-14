import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { ClientProvider } from "../client/ClientProvider";
import { MockHabitaClient } from "../client/MockHabitaClient";
import { RUTAS } from "../rutas";
import { rutasApp } from "./rutasApp";

// ScrollRestoration llama a scrollTo, que jsdom no implementa.
beforeAll(() => {
  window.scrollTo = () => {};
});

function montar(ruta: string) {
  const router = createMemoryRouter(rutasApp, { initialEntries: [ruta] });
  render(
    <ClientProvider client={new MockHabitaClient({ latenciaMs: 0 })}>
      <RouterProvider router={router} />
    </ClientProvider>,
  );
}

describe("rutas", () => {
  it.each([
    [RUTAS.inicio, /tu lugar en la CDMX/],
    [RUTAS.comoFunciona, /Así te ayudamos/],
    [RUTAS.colonias, /colonias piloto/],
    [RUTAS.preguntas, /Lo que nos preguntan/],
    [RUTAS.buscar, /Cuéntale a Habita qué buscas/],
    ["/no-existe", /se mudó o no existe/],
  ])("%s renderiza su h1", async (ruta, titulo) => {
    montar(ruta);
    expect(await screen.findByRole("heading", { level: 1, name: titulo })).toBeInTheDocument();
  });
});
