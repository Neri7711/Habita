import type { CSSProperties } from "react";
import s from "./Placeholder.module.css";

type PlaceholderProps = { fondo: string; etiqueta: string; alt: string; className?: string };

/** Fondo sólido de la escena con su nombre, para que se note que falta la ilustración. */
export function Placeholder({ fondo, etiqueta, alt, className }: PlaceholderProps) {
  return (
    <div
      role="img"
      aria-label={alt}
      className={[s.placeholder, className].filter(Boolean).join(" ")}
      style={{ "--fondo": fondo } as CSSProperties}
    >
      <span className={`${s.etiqueta} t-label`} aria-hidden="true">{etiqueta}</span>
    </div>
  );
}
