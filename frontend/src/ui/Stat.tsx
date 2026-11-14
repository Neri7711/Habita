import s from "./Stat.module.css";

type StatProps = { valor: number | string; etiqueta: string; sufijo?: string };

export function Stat({ valor, etiqueta, sufijo }: StatProps) {
  return (
    <div className={s.stat}>
      <span className="t-stat">{valor}{sufijo}</span>
      <span className={`${s.etiqueta} t-small`}>{etiqueta}</span>
    </div>
  );
}
