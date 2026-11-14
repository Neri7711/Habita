import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { MARCA } from "../brand";

/**
 * Pone "<Página> · Habita" en el título y, al navegar dentro del sitio, lleva el foco al h1 de la página.
 * En la primera carga (location.key === "default") no mueve el foco.
 */
export function useTituloPagina(pagina: string) {
  const { key } = useLocation();
  useEffect(() => {
    document.title = `${pagina} · ${MARCA}`;
    if (key === "default") return;
    const h1 = document.querySelector<HTMLElement>("main h1");
    if (!h1) return;
    h1.tabIndex = -1;
    h1.focus({ preventScroll: true });
  }, [pagina, key]);
}
