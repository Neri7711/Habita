import { useId, type InputHTMLAttributes } from "react";
import s from "./Input.module.css";

type InputProps = { etiqueta: string; error?: string } & InputHTMLAttributes<HTMLInputElement>;

export function Input({ etiqueta, error, className, id, ...resto }: InputProps) {
  const auto = useId();
  const inputId = id ?? auto;
  const errorId = `${inputId}-error`;
  return (
    <div className={[s.campo, className].filter(Boolean).join(" ")}>
      <label htmlFor={inputId} className={s.etiqueta}>{etiqueta}</label>
      <input
        {...resto}
        id={inputId}
        className={s.input}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
      />
      {error && <p id={errorId} className={s.error} role="alert">{error}</p>}
    </div>
  );
}
