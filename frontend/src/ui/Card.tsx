import type { HTMLAttributes } from "react";
import s from "./Card.module.css";

type CardProps = HTMLAttributes<HTMLDivElement> & { interactiva?: boolean };

export function Card({ interactiva = true, className, ...resto }: CardProps) {
  const clases = [s.card, interactiva && s.hover, className].filter(Boolean).join(" ");
  return <div {...resto} className={clases} />;
}
