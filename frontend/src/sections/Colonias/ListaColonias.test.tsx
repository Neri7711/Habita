import { render, screen } from "@testing-library/react";
import { ClientProvider } from "../../client/ClientProvider";
import { MockHabitaClient } from "../../client/MockHabitaClient";
import { ListaColonias } from "./Colonias";
import { useColonias } from "./useColonias";

function Lista() {
  return <ListaColonias estado={useColonias()} />;
}

describe("ListaColonias", () => {
  it("si falla muestra el error con Reintentar", async () => {
    render(
      <ClientProvider client={new MockHabitaClient({ latenciaMs: 0, fallar: true })}>
        <Lista />
      </ClientProvider>,
    );
    expect(await screen.findByText(/Fallo simulado/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });

  it("con datos agrupa por alcaldía", async () => {
    render(
      <ClientProvider client={new MockHabitaClient({ latenciaMs: 0 })}>
        <Lista />
      </ClientProvider>,
    );
    expect((await screen.findAllByRole("heading", { level: 2 })).length).toBeGreaterThan(0);
  });
});
