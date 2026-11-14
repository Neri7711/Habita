import { Link } from "react-router-dom";
import { RUTAS } from "../../rutas";
import { Logo } from "../Navbar/Logo";
import s from "./Footer.module.css";

const ENLACES = [
  { to: RUTAS.comoFunciona, texto: "Cómo funciona" },
  { to: RUTAS.colonias, texto: "Colonias" },
  { to: RUTAS.preguntas, texto: "Preguntas" },
  { to: RUTAS.buscar, texto: "Hablar con Habita" },
];

const FUENTES = "Datos Abiertos CDMX, INEGI (DENUE), Banxico, OpenStreetMap e Inside Airbnb";

export function Footer() {
  return (
    <footer className={s.raiz}>
      <div className={`contenedor ${s.interior}`}>
        <div className={s.fila}>
          <div className={s.marca}>
            <Logo />
            <p className="t-small">Un asesor que solo recomienda para mudarte a la CDMX.</p>
          </div>
          <nav aria-label="Pie de página">
            <ul className={s.enlaces}>
              {ENLACES.map((e) => (
                <li key={e.to}>
                  <Link to={e.to} className={s.enlace}>
                    {e.texto}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className={s.legal}>
          <p className="t-small">Fuentes de datos: {FUENTES}.</p>
          <p className="t-small">Habita recomienda; no es asesoría legal ni financiera.</p>
        </div>
      </div>
    </footer>
  );
}
