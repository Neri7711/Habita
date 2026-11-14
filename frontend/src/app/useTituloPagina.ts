import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { MARCA } from "../brand";

/**
 * Pone "<Página> · Habita" en el título y, al navegar dentro del sitio, lleva el foco al h1 de la página.
 * Si la URL trae hash (#ejemplo), el foco va a ese destino en vez del h1.
 * En la primera carga (location.key === "default") no mueve el foco.
 */
export function useTituloPagina(pagina: string) {
  const { key, hash } = useLocation();
  useEffect(() => {
    document.title = `${pagina} · ${MARCA}`;
    if (key === "default") return;
    const destino = hash
      ? document.getElementById(decodeURIComponent(hash.slice(1)))
      : document.querySelector<HTMLElement>("main h1");
    if (!destino) return;
    destino.tabIndex = -1;
    destino.focus({ preventScroll: true });
  }, [pagina, key, hash]);
}
