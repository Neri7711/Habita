import type { CSSProperties, ReactNode } from "react";
import { useReveal } from "../hooks";

type RevealProps = { retrasoMs?: number; children: ReactNode };

export function Reveal({ retrasoMs = 0, children }: RevealProps) {
  const [ref, visible] = useReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={`reveal ${visible ? "visible" : ""}`}
      style={{ "--retraso": `${retrasoMs}ms` } as CSSProperties}
    >
      {children}
    </div>
  );
}
