import { useRef, type KeyboardEvent } from "react";
import s from "./Toggle.module.css";

type Opcion<T extends string> = { valor: T; etiqueta: string };
type ToggleProps<T extends string> = {
  etiqueta: string;
  opciones: readonly Opcion<T>[];
  valor: T;
  onChange: (valor: T) => void;
  "aria-describedby"?: string;
};

const TECLAS: Record<string, number> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

// Radiogroup con roving tabindex: una sola parada de Tab y flechas para moverse (patrón WAI-ARIA).
export function Toggle<T extends string>({ etiqueta, opciones, valor, onChange, ...aria }: ToggleProps<T>) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const actual = opciones.findIndex((o) => o.valor === valor);
  const enfocable = actual === -1 ? 0 : actual;

  function onKeyDown(e: KeyboardEvent, i: number) {
    const paso = TECLAS[e.key];
    if (!paso) return;
    e.preventDefault();
    const siguiente = (i + paso + opciones.length) % opciones.length;
    onChange(opciones[siguiente].valor);
    refs.current[siguiente]?.focus();
  }

  return (
    <div role="radiogroup" aria-label={etiqueta} aria-describedby={aria["aria-describedby"]} className={s.grupo}>
      {opciones.map((o, i) => (
        <button
          key={o.valor}
          ref={(el) => { refs.current[i] = el; }}
          type="button"
          role="radio"
          aria-checked={o.valor === valor}
          tabIndex={i === enfocable ? 0 : -1}
          className={`${s.opcion} ${o.valor === valor ? s.activa : ""}`}
          onClick={() => onChange(o.valor)}
          onKeyDown={(e) => onKeyDown(e, i)}
        >
          {o.etiqueta}
        </button>
      ))}
    </div>
  );
}
