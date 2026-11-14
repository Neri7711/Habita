import { useId, useState, type ReactNode } from "react";
import s from "./Accordion.module.css";

type Item = { id: string; titulo: string; contenido: ReactNode };

/** Un item abierto a la vez. */
export function Accordion({ items }: { items: readonly Item[] }) {
  const [abierto, setAbierto] = useState<string | null>(null);
  const base = useId();
  return (
    <ul className={s.lista}>
      {items.map((it) => {
        const open = abierto === it.id;
        const panelId = `${base}-${it.id}`;
        return (
          <li key={it.id} className={`${s.item} ${open ? s.abierto : ""}`}>
            <h3 className={s.titulo}>
              <button
                type="button"
                className={s.boton}
                aria-expanded={open}
                aria-controls={panelId}
                onClick={() => setAbierto(open ? null : it.id)}
              >
                <span>{it.titulo}</span>
                <span className={s.icono} aria-hidden="true">+</span>
              </button>
            </h3>
            <div id={panelId} role="region" hidden={!open} className={s.panel}>
              {it.contenido}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
