import { useEffect, useState } from "react";

const coincide = (q: string) =>
  typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(q).matches;

export function useMediaQuery(query: string): boolean {
  const [ok, setOk] = useState(() => coincide(query));
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia(query);
    const alCambiar = () => setOk(mq.matches);
    alCambiar();
    mq.addEventListener("change", alCambiar);
    return () => mq.removeEventListener("change", alCambiar);
  }, [query]);
  return ok;
}
