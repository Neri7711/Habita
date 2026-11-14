/** Fachada sencilla de un edificio de depas, decorativa. */
export function IlustracionDepa({ className }: { className?: string }) {
  const ventanas = [0, 1, 2].flatMap((fila) =>
    [0, 1, 2].map((col) => ({ x: 92 + col * 44, y: 52 + fila * 40 })),
  );
  return (
    <svg viewBox="0 0 320 200" className={className} aria-hidden="true" focusable="false">
      <rect width="320" height="200" fill="var(--cielo)" />
      <rect y="176" width="320" height="24" fill="var(--stone)" />
      <rect x="76" y="32" width="168" height="144" fill="var(--paper)" />
      <rect x="76" y="24" width="168" height="8" fill="var(--tezontle)" />
      {ventanas.map((v) => (
        <rect key={`${v.x}-${v.y}`} x={v.x} y={v.y} width="28" height="24" fill="var(--xolo)" />
      ))}
      <rect x="146" y="148" width="28" height="28" fill="var(--tezontle-ink)" />
      <rect x="252" y="120" width="8" height="56" fill="var(--xolo)" />
      <circle cx="256" cy="112" r="22" fill="var(--arbol-morado)" />
      <rect x="44" y="132" width="6" height="44" fill="var(--xolo)" />
      <circle cx="47" cy="124" r="16" fill="var(--arbol-verde)" />
    </svg>
  );
}
