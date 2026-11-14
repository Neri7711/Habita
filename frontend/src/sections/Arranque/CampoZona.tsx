import { useId } from "react";
import { Button } from "../../ui";
import s from "./Arranque.module.css";
import type { EstadoZonas } from "./useZonas";

interface Props {
  estado: EstadoZonas;
  valor: string;
  onChange: (id: string) => void;
  error?: string;
  onReintentar: () => void;
}

/** "¿Dónde trabajas?" como <select> nativo alimentado por listarZonas(). */
export function CampoZona({ estado, valor, onChange, error, onReintentar }: Props) {
  const id = useId();
  const errorId = `${id}-error`;
  const cargaId = `${id}-carga`;
  const describedBy = [error && errorId, estado.fase === "error" && cargaId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={s.campoSelect}>
      <label htmlFor={id} className={s.etiqueta}>
        ¿Dónde trabajas?
      </label>
      <select
        id={id}
        className={s.select}
        value={valor}
        onChange={(e) => onChange(e.target.value)}
        disabled={estado.fase !== "listo"}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
      >
        {estado.fase === "cargando" ? (
          <option value="">Cargando zonas…</option>
        ) : (
          <option value="">Elige una zona</option>
        )}
        {estado.fase === "listo" &&
          estado.zonas.map((z) => (
            <option key={z.id} value={z.id}>
              {z.nombre}
            </option>
          ))}
      </select>
      {estado.fase === "error" && (
        <div id={cargaId} className={s.cargaError} role="status">
          <p className={s.error}>{estado.mensaje}</p>
          <Button type="button" variante="secundario" onClick={onReintentar}>
            Reintentar
          </Button>
        </div>
      )}
      {error && (
        <p id={errorId} className={s.error} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
