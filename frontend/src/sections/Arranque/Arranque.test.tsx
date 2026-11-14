import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ClientProvider } from "../../client/ClientProvider";
import { MockHabitaClient } from "../../client/MockHabitaClient";
import { Arranque } from "./Arranque";

function montar() {
  render(
    <ClientProvider client={new MockHabitaClient({ latenciaMs: 0 })}>
      <Arranque />
    </ClientProvider>,
  );
  return userEvent.setup();
}

describe("Arranque", () => {
  it("con un formulario válido pasa al chat y muestra opciones", async () => {
    const user = montar();
    await user.type(screen.getByLabelText(/presupuesto/i), "15,000");
    await user.type(screen.getByLabelText(/dónde trabajas/i), "Reforma");
    await user.click(screen.getByRole("radio", { name: "No" }));
    await user.click(screen.getByRole("button", { name: /buscar opciones/i }));

    expect(await screen.findByText(/Encontré \d+ opci(ón|ones) /)).toBeInTheDocument();
    expect(screen.getByText("Datos de ejemplo")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /editar mi búsqueda/i }));
    expect(screen.getByLabelText(/presupuesto/i)).toHaveValue("15,000");
  });

  it("con un formulario inválido muestra errores y enfoca el primer campo", async () => {
    const user = montar();
    await user.click(screen.getByRole("button", { name: /buscar opciones/i }));

    const presupuesto = screen.getByLabelText(/presupuesto/i);
    expect(presupuesto).toHaveAttribute("aria-invalid", "true");
    expect(presupuesto).toHaveFocus();
    expect(screen.getByText(/Indica si tienes mascotas/)).toBeInTheDocument();
    expect(screen.queryByText(/Tu búsqueda con Habita/)).not.toBeInTheDocument();
  });
});
