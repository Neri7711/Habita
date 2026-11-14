import caja from "../assets/ilustraciones/xolo-caja.svg";
import mapa from "../assets/ilustraciones/xolo-mapa.svg";
import recostado from "../assets/ilustraciones/xolo-recostado.svg";
import revisando from "../assets/ilustraciones/xolo-anuncios.svg";
import sentado from "../assets/ilustraciones/xolo-sentado.svg";
import { Placeholder } from "./Placeholder";
import s from "./XoloScene.module.css";

export type Escena = "mapa" | "revisando" | "caja" | "llaves" | "dormido" | "sentado" | "recostado";

/** Para sumar una escena: copia el SVG a assets/ilustraciones/, impórtalo y ponlo en `src`. Sin `src` se ve el Placeholder. */
const ESCENAS: Record<Escena, { src?: string; fondo: string }> = {
  caja: { src: caja, fondo: "var(--durazno)" },
  recostado: { src: recostado, fondo: "var(--sol)" },
  mapa: { src: mapa, fondo: "var(--durazno)" },
  revisando: { src: revisando, fondo: "var(--tezontle-soft)" },
  sentado: { src: sentado, fondo: "var(--sol)" },
  llaves: { fondo: "var(--sol)" },
  dormido: { fondo: "var(--durazno)" },
};

type XoloSceneProps = { escena: Escena; alt: string; className?: string };

export function XoloScene({ escena, alt, className }: XoloSceneProps) {
  const { src, fondo } = ESCENAS[escena];
  if (!src) return <Placeholder fondo={fondo} etiqueta={escena} alt={alt} className={className} />;
  return (
    <div className={[s.escena, className].filter(Boolean).join(" ")} style={{ background: fondo }}>
      <img src={src} alt={alt} className={s.img} loading="lazy" decoding="async" />
    </div>
  );
}
