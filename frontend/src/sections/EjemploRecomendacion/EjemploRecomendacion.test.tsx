import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClientProvider } from "../../client/ClientProvider";
import { MockHabitaClient } from "../../client/MockHabitaClient";
import { EjemploRecomendacion } from "./EjemploRecomendacion";

function montar(fallar: boolean) {
  render(
    <MemoryRouter>
      <ClientProvider client={new MockHabitaClient({ latenciaMs: 0, fallar })}>
        <EjemploRecomendacion />
      </ClientProvider>
    </MemoryRouter>,
  );
}

describe("EjemploRecomendacion", () => {
  it("si falla muestra el error con Reintentar", async () => {
    montar(true);
    expect(await screen.findByRole("status")).toHaveTextContent(/Fallo simulado/);
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });

  it("con datos muestra la tarjeta", async () => {
    montar(false);
    expect(await screen.findByText(/^Fuente:/)).toBeInTheDocument();
  });
});
