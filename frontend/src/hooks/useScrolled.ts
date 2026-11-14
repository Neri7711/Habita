import { useEffect, useState } from "react";

/** true cuando scrollY supera el umbral (8 px por defecto). */
export function useScrolled(umbral = 8): boolean {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const alScroll = () => setScrolled(window.scrollY > umbral);
    alScroll();
    window.addEventListener("scroll", alScroll, { passive: true });
    return () => window.removeEventListener("scroll", alScroll);
  }, [umbral]);
  return scrolled;
}
