import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "./useReducedMotion";

/** Devuelve [ref, visible]. Con reduced-motion o sin IntersectionObserver, visible desde el inicio. */
export function useReveal<T extends HTMLElement = HTMLDivElement>() {
  const ref = useRef<T>(null);
  const reducido = useReducedMotion();
  const sinObserver = typeof IntersectionObserver === "undefined";
  const [visto, setVisto] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || reducido || sinObserver) return;
    const obs = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) {
          setVisto(true);
          obs.disconnect();
        }
      },
      { threshold: 0.15 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [reducido, sinObserver]);

  return [ref, visto || reducido || sinObserver] as const;
}
