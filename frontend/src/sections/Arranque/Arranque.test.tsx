import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ClientProvider } from "../../client/ClientProvider";
import { MockHabitaClient } from "../../client/MockHabitaClient";
import { ZONAS_TRABAJO } from "../../domain";
import { Arranque } from "./Arranque";

function montar(client = new MockHabitaClient({ latenciaMs: 0 })) {
  render(
    <ClientProvider client={client}>
      <Arranque />
    </ClientProvider>,
  );
  return userEvent.setup();
}

describe("Arranque", () => {
  it("con un formulario válido pasa al chat y 'Editar' conserva presupuesto y zona", async () => {
    const user = montar();
    await screen.findByRole("option", { name: "Santa Fe" });
    await user.type(screen.getByLabelText(/presupuesto/i), "15,000");
    await user.selectOptions(screen.getByLabelText(/dónde trabajas/i), "santa-fe");
    await user.click(screen.getByRole("radio", { name: "No" }));
    await user.click(screen.getByRole("button", { name: /buscar opciones/i }));

    expect(await screen.findByText(/Encontré \d+ opci(ón|ones) /)).toBeInTheDocument();
    expect(screen.getByText("Datos de ejemplo")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /editar mi búsqueda/i }));
    expect(screen.getByLabelText(/presupuesto/i)).toHaveValue("15,000");
    expect(screen.getByLabelText(/dónde trabajas/i)).toHaveValue("santa-fe");
  });

  it("el select trae las zonas del cliente con 'Elige una zona' primero", async () => {
    montar();
    await screen.findByRole("option", { name: "Polanco" });
    const opciones = screen.getAllByRole("option");
    expect(opciones[0]).toHaveTextContent("Elige una zona");
    expect(opciones[0]).toHaveValue("");
    expect(opciones).toHaveLength(ZONAS_TRABAJO.length + 1);
  });

  it("mientras cargan las zonas el select está deshabilitado", () => {
    montar(new MockHabitaClient({ latenciaMs: 10_000 }));
    const select = screen.getByLabelText(/dónde trabajas/i);
    expect(select).toBeDisabled();
    expect(screen.getByRole("option", { name: "Cargando zonas…" })).toBeInTheDocument();
  });

  it("si fallan las zonas muestra el error y 'Reintentar'", async () => {
    montar(new MockHabitaClient({ latenciaMs: 0, fallar: true }));
    expect(await screen.findByText("Fallo simulado del cliente mock.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
    expect(screen.getByLabelText(/dónde trabajas/i)).toBeDisabled();
  });

  it("con un formulario inválido muestra errores y enfoca el primer campo", async () => {
    const user = montar();
    await screen.findByRole("option", { name: "Polanco" });
    await user.click(screen.getByRole("button", { name: /buscar opciones/i }));

    const presupuesto = screen.getByLabelText(/presupuesto/i);
    expect(presupuesto).toHaveAttribute("aria-invalid", "true");
    expect(presupuesto).toHaveFocus();
    expect(screen.getByText(/Indica si tienes mascotas/)).toBeInTheDocument();
    expect(screen.queryByText(/Tu búsqueda con Habita/)).not.toBeInTheDocument();
  });

  it("sin zona elegida marca el select y lo enfoca si es el primer error", async () => {
    const user = montar();
    await screen.findByRole("option", { name: "Polanco" });
    await user.type(screen.getByLabelText(/presupuesto/i), "15000");
    await user.click(screen.getByRole("button", { name: /buscar opciones/i }));

    const select = screen.getByLabelText(/dónde trabajas/i);
    expect(select).toHaveAttribute("aria-invalid", "true");
    expect(select).toHaveFocus();
    const error = screen.getByText("Elige la zona donde trabajas.");
    expect(select.getAttribute("aria-describedby")).toContain(error.id);
  });
});
