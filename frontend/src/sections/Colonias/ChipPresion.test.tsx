import { render, screen } from "@testing-library/react";
import { ChipPresion } from "./Colonias";

describe("ChipPresion", () => {
  it.each([
    [0.83, "Alta (0.83 de 1)"],
    [0.6, "Media (0.60 de 1)"],
    [0.2, "Baja (0.20 de 1)"],
    [null, "Sin dato"],
    [undefined, "Sin dato"],
  ])("%s → %s", (valor, texto) => {
    render(<ChipPresion valor={valor} />);
    expect(screen.getByText(texto)).toBeInTheDocument();
  });
});
