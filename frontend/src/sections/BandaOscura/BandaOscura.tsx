import { Greca, type VarianteGreca } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Button, Reveal } from "../../ui";
import s from "./BandaOscura.module.css";

const GRECAS: VarianteGreca[] = ["A", "C", "E", "B", "D", "C"];

export function BandaOscura() {
  return (
    <section aria-labelledby="banda-titulo" className="contenedor seccion">
      <Reveal>
        <div className={s.bloque}>
          <div className={s.grecas} aria-hidden="true">
            {GRECAS.map((v, i) => (
              <Greca key={i} variante={v} className={s.greca} />
            ))}
          </div>
          <h2 id="banda-titulo" className={`${s.titulo} t-h2`}>
            ¿Listo para encontrar tu <span className={s.acento}>lugar</span>?
          </h2>
          <Button variante="secundario" sobre="ink" to={RUTAS.buscar} flecha>
            Hablar con Habita
          </Button>
        </div>
      </Reveal>
    </section>
  );
}
