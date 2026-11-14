import { Link } from "react-router-dom";
import { Greca, type VarianteGreca } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Card, Pill, Reveal } from "../../ui";
import s from "./Pilares.module.css";

const PASO_MS = 60;

const PILARES: { titulo: string; texto: string; greca: VarianteGreca }[] = [
  { titulo: "Costo real de vivir", texto: "Renta más transporte más tiempo: lo que de verdad te cuesta cada colonia al mes.", greca: "A" },
  { titulo: "Precio justo", texto: "Comparamos el precio del anuncio con lo que se pide en la misma colonia.", greca: "B" },
  { titulo: "Confianza del anuncio", texto: "Señales de fraude explicadas en lenguaje simple, antes de que des un peso.", greca: "C" },
  { titulo: "Encaje con la comunidad", texto: "Mercados, parques y vida cultural cerca, para que sepas cómo se vive ahí.", greca: "D" },
  { titulo: "Reubicación consciente", texto: "Te avisamos si una colonia tiene presión de gentrificación y qué significa.", greca: "E" },
];

/** `resumen`: solo 3 cards y un enlace a la página con los 5 (Inicio). */
export function Pilares({ resumen = false }: { resumen?: boolean }) {
  const pilares = resumen ? PILARES.slice(0, 3) : PILARES;
  return (
    <section id="que-explicamos" className="seccion" aria-labelledby="pilares-titulo">
      <div className="contenedor">
        <Reveal>
          <header className={s.cabecera}>
            <div className={s.encabezado}>
              <Pill punto>QUÉ TE EXPLICAMOS</Pill>
              <h2 id="pilares-titulo" className="t-h2">Cinco cosas que revisamos antes de recomendarte</h2>
            </div>
            {/* En la página completa el ejemplo va justo debajo: no hace falta enlace. */}
            {resumen && (
              <Link to={`${RUTAS.comoFunciona}#que-explicamos`} className={s.link}>
                Ver los 5 <span aria-hidden="true">→</span>
              </Link>
            )}
          </header>
        </Reveal>
        <ul className={s.grid}>
          {pilares.map((p, i) => (
            <li key={p.titulo} className={s.celda}>
              <Reveal retrasoMs={PASO_MS * (i + 1)}>
                <Card className={s.card}>
                  <div className={s.marca}>
                    <span className={s.greca}>
                      <Greca variante={p.greca} />
                    </span>
                    <span className={`t-label ${s.numero}`} aria-hidden="true">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className={`t-h3 ${s.titulo}`}>{p.titulo}</h3>
                  <p className={`t-body ${s.texto}`}>{p.texto}</p>
                </Card>
              </Reveal>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
