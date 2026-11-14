import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import heroIslas from "../../assets/ilustraciones/hero-islas-cdmx.svg";
import xolo from "../../assets/ilustraciones/xolo-recostado.svg";
import { useClient } from "../../client/useClient";
import { useProgresoScroll } from "../../hooks/useProgresoScroll";
import { RUTAS } from "../../rutas";
import { Button, Card } from "../../ui";
import s from "./Hero.module.css";

/** Centro de cada etiqueta sobre su isla, en % de hero-islas-cdmx.svg (1200×720). Se mueven con la imagen. */
const ISLAS = [
  { nombre: "Centro", left: "28%", top: "13%" },
  { nombre: "Roma–Condesa", left: "69%", top: "7%" },
  { nombre: "Coyoacán", left: "52%", top: "49%" },
];

/** Cuenta las colonias piloto desde el cliente; null mientras carga o si falla. */
function useConteoColonias(): number | null {
  const client = useClient();
  const [n, setN] = useState<number | null>(null);
  useEffect(() => {
    let vivo = true;
    client
      .listarColonias()
      .then((c) => vivo && setN(c.length))
      .catch(() => vivo && setN(null));
    return () => {
      vivo = false;
    };
  }, [client]);
  return n;
}

export function Hero() {
  const n = useConteoColonias();
  const fondoRef = useRef<HTMLDivElement>(null);
  useProgresoScroll(fondoRef);

  return (
    <section className={s.raiz} aria-labelledby="hero-titulo">
      {/* Cielo a sangre detrás del navbar; al hacer scroll se recorta hasta la caja redondeada del contenedor. */}
      <div ref={fondoRef} className={s.fondo} aria-hidden="true" />

      <div className={`contenedor ${s.contenido}`}>
        <div className={s.texto}>
          <h1 id="hero-titulo" className={`t-hero ${s.titular}`}>
            <span className="resaltada">Encuentra</span> tu lugar en la CDMX sin adivinar
          </h1>
          <p className={`t-body-lg ${s.bajada}`}>
            Te decimos cuánto cuesta vivir de verdad, si el precio es justo y si el anuncio es confiable.
          </p>
          <div className={s.acciones}>
            <Button variante="primario" to={RUTAS.buscar} flecha>
              Empezar mi búsqueda
            </Button>
            <Link to={RUTAS.comoFunciona} className={s.secundario}>
              Ver cómo funciona
            </Link>
          </div>
        </div>

        <div className={s.arte}>
          <div className={s.islas}>
            <img src={heroIslas} alt="" className={s.imagen} width={1200} height={720} decoding="async" />
            {ISLAS.map((isla) => (
              <span key={isla.nombre} className={`t-label ${s.etiqueta}`} style={{ left: isla.left, top: isla.top }}>
                {isla.nombre}
              </span>
            ))}
          </div>

          <Card interactiva={false} className={s.tarjeta}>
            <img src={xolo} alt="" className={s.xolo} width={48} height={48} decoding="async" />
            <p className="t-small">
              <strong>{n === null ? "Colonias piloto" : `${n} colonias piloto`}</strong>
              <span className={s.fuente}>Datos abiertos y fuentes citadas</span>
            </p>
          </Card>
        </div>
      </div>
    </section>
  );
}
