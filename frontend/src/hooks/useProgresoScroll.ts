import { useEffect, type RefObject } from "react";
import { useReducedMotion } from "./useReducedMotion";

/**
 * Escribe en `--progreso` (0→1) cuánto se ha recorrido de los primeros `distancia` px de scroll.
 * Va directo al estilo del elemento: sin estado de React ni re-renders. Un rAF por frame como máximo.
 * Con reduced motion fija 1 (estado final) y no escucha el scroll.
 */
export function useProgresoScroll(ref: RefObject<HTMLElement | null>, distancia = 150): void {
  const reducido = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const escribir = (p: number) => el.style.setProperty("--progreso", p.toFixed(3));

    if (reducido) {
      escribir(1);
      return;
    }

    let frame = 0;
    const medir = () => {
      frame = 0;
      escribir(Math.min(Math.max(window.scrollY / distancia, 0), 1));
    };
    const alScroll = () => {
      if (!frame) frame = requestAnimationFrame(medir);
    };

    medir();
    window.addEventListener("scroll", alScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", alScroll);
      cancelAnimationFrame(frame);
    };
  }, [ref, distancia, reducido]);
}
