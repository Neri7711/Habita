import { XoloScene, type Escena } from "../../illustrations";
import { Reveal } from "../../ui";
import s from "./ComoFunciona.module.css";

const PASO_MS = 60;

const PASOS: { escena: Escena; titulo: string; texto: string; alt: string }[] = [
  {
    escena: "mapa",
    titulo: "Cuéntanos qué buscas",
    texto: "Presupuesto, dónde trabajas y cómo quieres vivir.",
    alt: "El Xolo de Habita sostiene un mapa de la Ciudad de México sobre fondo durazno.",
  },
  {
    escena: "revisando",
    titulo: "Comparamos por ti",
    texto: "Revisamos precios, costos y señales de cada anuncio.",
    alt: "El Xolo de Habita revisa anuncios de departamentos en una laptop.",
  },
  {
    escena: "caja",
    titulo: "Elige con confianza",
    texto: "Decides tú, con cada recomendación explicada.",
    alt: "El Xolo de Habita asoma desde una caja de mudanza, listo para su nuevo hogar.",
  },
];

/**
 * Pasos de onboarding. Vive justo debajo del h1 de "Cómo funciona", así que su h2 es solo
 * para lectores de pantalla: visualmente manda el número de cada paso.
 */
export function ComoFunciona() {
  return (
    <section id="como-funciona" className="seccion" aria-labelledby="como-titulo">
      <div className="contenedor">
        <h2 id="como-titulo" className="sr-only">Tres pasos, sin adivinar</h2>
        <ol className={s.pasos}>
          {PASOS.map((p, i) => (
            <li key={p.escena} className={s.paso}>
              <Reveal retrasoMs={PASO_MS * i}>
                <XoloScene escena={p.escena} alt={p.alt} className={s.escena} />
                <div className={s.pie}>
                  <span className={`t-stat ${s.numero}`} aria-hidden="true">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h3 className="t-h3">{p.titulo}</h3>
                    <p className={`t-body ${s.texto}`}>{p.texto}</p>
                  </div>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
