import { useEffect, useState } from "react";
import { useClient } from "../../client/useClient";
import type { StatsLanding } from "../../domain";
import { XoloScene } from "../../illustrations";
import { Pill, Reveal, Stat } from "../../ui";
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
  const client = useClient();
  const [stats, setStats] = useState<StatsLanding | null>(null);

  useEffect(() => {
    let vigente = true;
    client.obtenerStats().then((r) => vigente && setStats(r), () => undefined);
    return () => {
      vigente = false;
    };
  }, [client]);

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
            <ul className={s.stats} aria-busy={stats === null}>
              {filasDeStats(stats).map((f) => (
                <li key={f.etiqueta} className={s.stat}>
                  <Stat valor={f.valor} sufijo={f.sufijo} etiqueta={f.etiqueta} />
                </li>
              ))}
            </ul>
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
