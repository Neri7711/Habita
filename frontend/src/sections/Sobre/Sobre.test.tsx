import { render, screen } from "@testing-library/react";
import { ClientProvider } from "../../client/ClientProvider";
import { MockHabitaClient } from "../../client/MockHabitaClient";
import { Sobre } from "./Sobre";

describe("Sobre", () => {
  it("si las cifras fallan muestra el error, ofrece Reintentar y deja de estar ocupado", async () => {
    render(
      <ClientProvider client={new MockHabitaClient({ latenciaMs: 0, fallar: true })}>
        <Sobre />
      </ClientProvider>,
    );
    expect(await screen.findByRole("status")).toHaveTextContent(/Fallo simulado/);
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
    expect(screen.getByRole("list")).toHaveAttribute("aria-busy", "false");
  });

  it("con datos muestra las cifras del cliente", async () => {
    render(
      <ClientProvider client={new MockHabitaClient({ latenciaMs: 0 })}>
        <Sobre />
      </ClientProvider>,
    );
    expect(await screen.findByText("colonias piloto")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reintentar" })).not.toBeInTheDocument();
  });
});
