import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useScrolled } from "../../hooks";
import { RUTAS } from "../../rutas";
import { Logo } from "./Logo";
import s from "./Navbar.module.css";

const ENLACES = [
  { to: RUTAS.comoFunciona, texto: "Cómo funciona" },
  { to: RUTAS.colonias, texto: "Colonias" },
  { to: RUTAS.preguntas, texto: "Preguntas" },
];

const UMBRAL_FLOTANTE = 320;

export function Navbar() {
  const scrolled = useScrolled();
  // El "Hablar" flotante (móvil) aparece tras el primer pantallazo: arriba ya están los CTAs del hero/encabezado.
  const conFlotante = useScrolled(UMBRAL_FLOTANTE);
  const { pathname } = useLocation();
  const [abierto, setAbierto] = useState(false);
  const botonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!abierto) return;
    const alTecla = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      setAbierto(false);
      botonRef.current?.focus();
    };
    document.addEventListener("keydown", alTecla);
    return () => document.removeEventListener("keydown", alTecla);
  }, [abierto]);

  const cerrar = () => setAbierto(false);
  const enlaces = (clase: string) =>
    ENLACES.map((e) => (
      <li key={e.to}>
        <NavLink to={e.to} className={clase} onClick={cerrar}>
          {e.texto}
        </NavLink>
      </li>
    ));

  return (
    <header className={[s.raiz, (scrolled || abierto) && s.solida].filter(Boolean).join(" ")}>
      <nav className={`contenedor ${s.barra}`} aria-label="Principal">
        <Link to={RUTAS.inicio} className={s.logo} aria-label="Habita, ir al inicio" onClick={cerrar}>
          <Logo />
        </Link>

        <ul className={s.enlaces}>{enlaces(s.enlace)}</ul>

        <Link to={RUTAS.buscar} className={`${s.hablar} ${s.soloEscritorio}`}>
          Hablar con Habita
        </Link>

        <button
          ref={botonRef}
          type="button"
          className={s.hamburguesa}
          aria-expanded={abierto}
          aria-controls="menu-movil"
          aria-label={abierto ? "Cerrar menú" : "Abrir menú"}
          onClick={() => setAbierto((v) => !v)}
        >
          <span className={s.lineas} aria-hidden="true" />
        </button>
      </nav>

      <div id="menu-movil" className={s.menuMovil} hidden={!abierto}>
        <ul className="contenedor">{enlaces(s.enlaceMovil)}</ul>
      </div>

      {pathname !== RUTAS.buscar && (
        <Link
          to={RUTAS.buscar}
          className={[s.hablar, s.flotante, conFlotante && s.flotanteVisible].filter(Boolean).join(" ")}
          onClick={cerrar}
        >
          Hablar
        </Link>
      )}
    </header>
  );
}
