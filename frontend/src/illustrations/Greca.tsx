export type VarianteGreca = "A" | "B" | "C" | "D" | "E";

// Grecas escalonadas (xicalcoliuhqui) simples, viewBox 64x32.
const TRAZOS: Record<VarianteGreca, string> = {
  A: "M4 28 H28 V8 H16 V18 H22 M36 28 H60 V8 H48 V18 H54",
  B: "M4 28 V4 H32 V20 H20 V12 M60 28 V4 H44",
  C: "M4 28 H12 V20 H20 V12 H28 V4 H36 V12 H44 V20 H52 V28 H60",
  D: "M4 4 H60 V28 H20 V16 H44 V12 H32",
  E: "M4 28 V16 H16 V4 H28 V16 H40 V4 H52 V16 H60 V28",
};

type GrecaProps = { variante: VarianteGreca; className?: string; color?: string };

export function Greca({ variante, className, color = "var(--tezontle)" }: GrecaProps) {
  return (
    <svg
      viewBox="0 0 64 32"
      width="64"
      height="32"
      className={className}
      aria-hidden="true"
      focusable="false"
      fill="none"
      stroke={color}
      strokeWidth="4"
      strokeLinejoin="miter"
      strokeLinecap="square"
    >
      <path d={TRAZOS[variante]} />
    </svg>
  );
}
