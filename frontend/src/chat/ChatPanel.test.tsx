import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ClientProvider } from "../client/ClientProvider";
import { MockHabitaClient } from "../client/MockHabitaClient";
import type { PerfilRapido } from "../domain";
import { ChatPanel } from "./ChatPanel";

const perfil: PerfilRapido = { operacion: "renta", presupuesto_max_mxn: 20000, destino_trabajo: "polanco", mascotas: false };

function montar(client: MockHabitaClient) {
  render(
    <ClientProvider client={client}>
      <ChatPanel perfil={perfil} onEditar={() => undefined} />
    </ClientProvider>,
  );
}

describe("ChatPanel", () => {
  it("muestra el nombre de la zona, los supuestos, los avisos y las fuentes", async () => {
    montar(new MockHabitaClient({ latenciaMs: 0 }));

    expect(await screen.findByText(/Trabajo en Polanco/)).toBeInTheDocument();
    expect(screen.getByText("Asumimos que…")).toBeInTheDocument();
    expect(screen.getByText(/Prioridades: precio/)).toBeInTheDocument();
    expect(screen.getByText(/no son ofertas reales/)).toBeInTheDocument();
    expect(screen.getByText(/Catálogo de ejemplo de Habita/)).toBeInTheDocument();
  });

  it("si la búsqueda falla muestra el error dentro del chat y ofrece Reintentar", async () => {
    montar(new MockHabitaClient({ latenciaMs: 0, fallar: true }));

    expect(await screen.findByText(/Fallo simulado del cliente mock/)).toBeInTheDocument();
    expect(screen.getByRole("log")).toHaveAttribute("aria-busy", "false");
    await userEvent.setup().click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText(/Fallo simulado del cliente mock/)).toBeInTheDocument();
  });
});
