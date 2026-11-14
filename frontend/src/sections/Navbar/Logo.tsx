import { MARCA } from "../../brand";

/** Casita-xolo: techo con dos orejas triangulares. Usa currentColor (sirve en claro y sobre ink). */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={className} style={{ display: "inline-flex", alignItems: "center", gap: "var(--sp-2)" }}>
      <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true" fill="currentColor">
        <path d="M5 4l5 5-5 3z M23 4l-5 5 5 3z" />
        <path d="M14 6L3 14.5V25h8v-6h6v6h8V14.5z" />
      </svg>
      <span style={{ font: "800 20px/1 var(--font-display)", letterSpacing: "-0.02em" }}>{MARCA}</span>
    </span>
  );
}
