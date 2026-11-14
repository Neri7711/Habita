import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from "react";
import { Link } from "react-router-dom";
import s from "./Button.module.css";

type Base = { variante: "primario" | "secundario"; sobre?: "claro" | "ink"; flecha?: boolean };
type Anchor = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href">;
type ButtonProps = Base & { href?: undefined; to?: undefined } & ButtonHTMLAttributes<HTMLButtonElement>;
/** Enlace externo. */
type HrefProps = Base & { href: string; to?: undefined } & Anchor;
/** Navegación interna: usa una ruta de `RUTAS`. */
type ToProps = Base & { to: string; href?: undefined } & Anchor;

export function Button(props: ButtonProps | HrefProps | ToProps) {
  const { variante, sobre = "claro", flecha, className, children, ...resto } = props;
  const clases = [s.btn, s[variante], s[sobre], className].filter(Boolean).join(" ");
  const contenido = (
    <>
      {children}
      {flecha && <span className={s.flecha} aria-hidden="true">→</span>}
    </>
  );
  if (props.to !== undefined) {
    const { to, ...a } = resto as Anchor & { to: string };
    return <Link {...a} to={to} className={clases}>{contenido}</Link>;
  }
  if (props.href !== undefined) {
    const a = resto as AnchorHTMLAttributes<HTMLAnchorElement>;
    return <a {...a} className={clases}>{contenido}</a>;
  }
  const b = resto as ButtonHTMLAttributes<HTMLButtonElement>;
  return <button type="button" {...b} className={clases}>{contenido}</button>;
}
