import { act, render } from "@testing-library/react";
import { useRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { useProgresoScroll } from "./useProgresoScroll";

function Prueba() {
  const ref = useRef<HTMLDivElement>(null);
  useProgresoScroll(ref, 100);
  return <div ref={ref} data-testid="el" />;
}

const progreso = (el: HTMLElement) => el.style.getPropertyValue("--progreso");
let pendientes: FrameRequestCallback[] = [];
const irA = (y: number) => {
  Object.defineProperty(window, "scrollY", { value: y, configurable: true });
  window.dispatchEvent(new Event("scroll"));
  pendientes.splice(0).forEach((cb) => cb(0));
};

beforeEach(() => {
  pendientes = [];
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((cb) => pendientes.push(cb));
});
afterEach(() => {
  vi.restoreAllMocks();
  irA(0);
});

it("calcula al montar y se acota entre 0 y 1 al hacer scroll", () => {
  irA(0);
  const { getByTestId } = render(<Prueba />);
  const el = getByTestId("el");
  expect(progreso(el)).toBe("0.000");

  act(() => irA(50));
  expect(progreso(el)).toBe("0.500");

  act(() => irA(400));
  expect(progreso(el)).toBe("1.000");
});

it("deja de escuchar al desmontar", () => {
  const quitar = vi.spyOn(window, "removeEventListener");
  const { unmount } = render(<Prueba />);
  unmount();
  expect(quitar).toHaveBeenCalledWith("scroll", expect.any(Function));
});
