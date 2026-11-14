import type { ReactNode } from "react";
import s from "./Chip.module.css";

type ChipProps = { variante: "neutro" | "confianza" | "alerta" | "ia"; children: ReactNode };

export function Chip({ variante, children }: ChipProps) {
  return <span className={`${s.chip} ${s[variante]}`}>{children}</span>;
}
