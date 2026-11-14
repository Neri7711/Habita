import { useClient } from "../../client/useClient";
import { XoloScene } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Button, Card, Chip, Reveal } from "../../ui";
import { agruparPorAlcaldia } from "./agruparPorAlcaldia";
import type { EstadoColonias } from "./useColonias";
import s from "./Colonias.module.css";

const plural = (n: number) => `${n} ${n === 1 ? "colonia" : "colonias"}`;

/** Indicador 0–1 calculado por el back (spec 02). Mismo umbral de "alta" (0.75) que las tarjetas de búsqueda. */
export function ChipPresion({ valor }: { valor?: number | null }) {
  if (valor === null || valor === undefined) return <Chip variante="neutro">Sin dato</Chip>;
  const nivel = valor >= 0.75 ? "Alta" : valor >= 0.5 ? "Media" : "Baja";
  return (
    <Chip variante={nivel === "Alta" ? "alerta" : "neutro"}>
      {nivel} ({valor.toFixed(2)} de 1)
    </Chip>
  );
}

/** Lista de colonias piloto por alcaldía. No muestra `hipotesis_presion` ni `rol` (hipótesis del equipo). */
export function ListaColonias({ estado }: { estado: EstadoColonias }) {
  const { origen } = useClient();

  return (
    <section aria-label="Colonias por alcaldía" className="banda-paper">
      <div className="contenedor seccion">
        {estado.tipo === "cargando" && (
          <p className={`${s.nota} t-small`} role="status">
            Cargando colonias…
          </p>
        )}
        {estado.tipo === "error" && (
          <div className={s.error} role="status">
            <p className={`${s.nota} t-small`}>{estado.mensaje}</p>
            <Button variante="secundario" onClick={estado.reintentar}>
              Reintentar
            </Button>
          </div>
        )}
        {estado.tipo === "listo" && (
          <div className={s.grupos}>
            {origen === "mock" && (
              <p>
                <Chip variante="neutro">Datos de ejemplo</Chip>
              </p>
            )}
            {agruparPorAlcaldia(estado.datos).map(({ alcaldia, colonias }, i) => (
              <Reveal key={alcaldia} retrasoMs={i * 60}>
                <section aria-labelledby={`alcaldia-${i}`} className={s.grupo}>
                  <h2 id={`alcaldia-${i}`} className={`t-h2 ${s.alcaldia}`}>
                    {alcaldia} <span className={`t-body ${s.conteo}`}>{plural(colonias.length)}</span>
                  </h2>
                  <ul className={s.grid} role="list">
                    {colonias.map((c) => (
                      <li key={c.colonia}>
                        <Card interactiva={false} className={s.card}>
                          <h3 className="t-h3">{c.colonia}</h3>
                          <dl className={s.dato}>
                            <dt className="t-small">Presión de gentrificación</dt>
                            <dd>
                              <ChipPresion valor={c.presion_gentrificacion} />
                            </dd>
                          </dl>
                        </Card>
                      </li>
                    ))}
                  </ul>
                </section>
              </Reveal>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/** Cierre de la página: un solo CTA primario a /buscar. */
export function CierreColonias() {
  return (
    <section aria-labelledby="colonias-cierre" className="banda-surface">
      <div className="contenedor seccion">
        <Reveal>
          <Card interactiva={false} className={s.cierre}>
            <div className={s.cierreTexto}>
              <h2 id="colonias-cierre" className="t-h2">
                ¿Ya tienes alguna en mente?
              </h2>
              <p className={`${s.nota} t-body-lg`}>
                Cuéntale a Habita tu presupuesto y dónde trabajas; te decimos qué opciones encajan en estas
                colonias.
              </p>
              <Button variante="primario" to={RUTAS.buscar} flecha>
                Buscar en estas colonias
              </Button>
            </div>
            <XoloScene escena="mapa" alt="" className={s.escena} />
          </Card>
        </Reveal>
      </div>
    </section>
  );
}
