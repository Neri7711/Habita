import { useClient } from "../../client/useClient";
import { XoloScene } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Button, Card, Chip, Reveal } from "../../ui";
import { agruparPorAlcaldia } from "./agruparPorAlcaldia";
import type { EstadoColonias } from "./useColonias";
import s from "./Colonias.module.css";

const plural = (n: number) => `${n} ${n === 1 ? "colonia" : "colonias"}`;

/** Lista de colonias piloto por alcaldía. No muestra `hipotesis_presion` ni `rol` (hipótesis del equipo). */
export function ListaColonias({ estado }: { estado: EstadoColonias }) {
  const { origen } = useClient();

  return (
    <section aria-label="Colonias por alcaldía" className="banda-paper">
      <div className="contenedor seccion">
        {estado === "cargando" && (
          <p className={`${s.nota} t-small`} role="status">
            Cargando colonias…
          </p>
        )}
        {estado === "error" && (
          <p className={`${s.nota} t-small`} role="status">
            No pudimos cargar las colonias. Intenta recargar la página.
          </p>
        )}
        {Array.isArray(estado) && (
          <div className={s.grupos}>
            {origen === "mock" && (
              <p>
                <Chip variante="neutro">Datos de ejemplo</Chip>
              </p>
            )}
            {agruparPorAlcaldia(estado).map(({ alcaldia, colonias }, i) => (
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
                              <Chip variante="neutro">Próximamente</Chip>
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
