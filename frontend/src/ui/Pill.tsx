import s from "./Pill.module.css";

type PillProps = { punto?: boolean; children: string };

export function Pill({ punto, children }: PillProps) {
  return (
    <span className={`${s.pill} t-label`}>
      {punto && <span className={s.punto} aria-hidden="true" />}
      {children}
    </span>
  );
}
