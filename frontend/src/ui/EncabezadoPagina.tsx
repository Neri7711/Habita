import type { ReactNode } from "react";
import { Pill } from "./Pill";
import s from "./EncabezadoPagina.module.css";

type EncabezadoPaginaProps = { pill: string; titulo: ReactNode; bajada?: ReactNode };

/** Apertura de las páginas internas: pill + h1 + bajada (habita-diseno-web.md §3). */
export function EncabezadoPagina({ pill, titulo, bajada }: EncabezadoPaginaProps) {
  return (
    <header className={`contenedor ${s.raiz}`}>
      <Pill punto>{pill}</Pill>
      <h1 className="t-h1">{titulo}</h1>
      {bajada && <p className={`t-body-lg ${s.bajada}`}>{bajada}</p>}
    </header>
  );
}
