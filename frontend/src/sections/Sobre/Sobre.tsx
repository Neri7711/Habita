import type { StatsLanding } from "../../domain";
import { XoloScene } from "../../illustrations";
import { Button, Pill, Reveal, Stat } from "../../ui";
import { useCarga } from "../Colonias/useCarga";
import s from "./Sobre.module.css";

const PASO_MS = 60;

function filasDeStats(stats: StatsLanding | null) {
  return [
    { valor: stats?.colonias ?? "—", etiqueta: "colonias piloto" },
    { valor: stats?.anuncios ?? "—", etiqueta: "anuncios revisados" },
    { valor: stats?.porcentajeExplicado ?? "—", sufijo: stats ? "%" : undefined, etiqueta: "recomendaciones con su porqué" },
  ];
}

export function Sobre() {
  const carga = useCarga((c) => c.obtenerStats());
  const stats = carga.tipo === "listo" ? carga.datos : null;

  const esEjemplo = stats?.origen === "mock";

  return (
    <section className="seccion" aria-labelledby="sobre-titulo">
      <div className={`contenedor ${s.grid}`}>
        <div className={s.texto}>
          <Reveal>
            <Pill punto>SOBRE HABITA</Pill>
          </Reveal>
          <Reveal retrasoMs={PASO_MS}>
            <h2 id="sobre-titulo" className={`t-h2 ${s.titulo}`}>Un asesor que solo recomienda</h2>
          </Reveal>
          <Reveal retrasoMs={PASO_MS * 2}>
            <p className={`t-body-lg ${s.parrafo}`}>
              No publicamos inmuebles, no cobramos comisión, no contactamos caseros. Te explicamos cada colonia y
              cada anuncio para que decidas tú, con datos y sin presión.
            </p>
          </Reveal>
          <Reveal retrasoMs={PASO_MS * 3}>
            <ul className={s.stats} aria-busy={carga.tipo === "cargando"}>
              {filasDeStats(stats).map((f) => (
                <li key={f.etiqueta} className={s.stat}>
                  <Stat valor={f.valor} sufijo={f.sufijo} etiqueta={f.etiqueta} />
                </li>
              ))}
            </ul>
            {carga.tipo === "error" && (
              <div className={s.error} role="status">
                <p className="t-small">{carga.mensaje}</p>
                <Button variante="secundario" onClick={carga.reintentar}>
                  Reintentar
                </Button>
              </div>
            )}
            {esEjemplo && (
              <p className={`t-small ${s.nota}`}>Datos de ejemplo: cifras provisionales mientras conectamos los datos reales.</p>
            )}
          </Reveal>
        </div>
        <Reveal retrasoMs={PASO_MS * 2}>
          <XoloScene escena="recostado" alt="" className={s.escena} />
        </Reveal>
      </div>
    </section>
  );
}
