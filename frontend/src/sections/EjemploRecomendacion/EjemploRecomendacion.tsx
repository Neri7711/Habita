import { useClient } from "../../client/useClient";
import type { RecomendacionEjemplo } from "../../domain";
import { XoloScene } from "../../illustrations";
import { formatMXN } from "../../lib/format";
import { RUTAS } from "../../rutas";
import { Button, Card, Chip, Pill, Reveal } from "../../ui";
import { useCarga, type Carga } from "../Colonias/useCarga";
import { IlustracionDepa } from "./IlustracionDepa";
import s from "./EjemploRecomendacion.module.css";

export function EjemploRecomendacion() {
  const client = useClient();
  const estado = useCarga((c) => c.obtenerEjemplo());

  return (
    <section id="ejemplo" aria-labelledby="ejemplo-titulo" className="contenedor seccion">
      <Reveal>
        <header className={s.encabezado}>
          <Pill punto>Ejemplo</Pill>
          <h2 id="ejemplo-titulo" className="t-h2">
            Así te recomienda Habita
          </h2>
          {client.origen === "mock" && <Chip variante="neutro">Datos de ejemplo</Chip>}
        </header>
      </Reveal>

      <div className={s.grid}>
        <Reveal>
          <ChatMock />
        </Reveal>
        <Reveal retrasoMs={60}>
          <TarjetaRecomendacion estado={estado} />
        </Reveal>
      </div>

      <Reveal>
        <div className={s.cierre}>
          <p className="t-body-lg">¿Quieres ver una recomendación hecha para ti?</p>
          <Button variante="primario" to={RUTAS.buscar} flecha>
            Probar con mi búsqueda
          </Button>
        </div>
      </Reveal>
    </section>
  );
}

function ChatMock() {
  return (
    <div className={s.chat} aria-label="Conversación de ejemplo con Habita" role="group">
      <p className={s.usuario}>
        Me mudo a la CDMX por trabajo. Busco depa de 2 recámaras, hasta $17,000 al mes y cerca de
        Insurgentes.
      </p>
      <div className={s.agente}>
        <div className={s.avatar}>
          <XoloScene escena="recostado" alt="" />
        </div>
        <div className={s.respuesta}>
          <span className={s.autor}>
            Habita <Chip variante="ia">IA</Chip>
          </span>
          <p>
            Te encontré una opción en Narvarte Poniente. El precio está en línea con la colonia y el
            anuncio no tiene señales de alerta. Te explico de dónde sale cada dato.
          </p>
        </div>
      </div>
    </div>
  );
}

function TarjetaRecomendacion({ estado }: { estado: Carga<RecomendacionEjemplo> }) {
  if (estado.tipo === "cargando") {
    return (
      <Card interactiva={false} className={s.tarjeta} aria-busy="true">
        <div className={s.esqueleto} />
        <p className={`${s.fuente} t-small`}>Cargando ejemplo…</p>
      </Card>
    );
  }
  if (estado.tipo === "error") {
    return (
      <Card interactiva={false} className={s.tarjeta} role="status">
        <p className="t-small">{estado.mensaje}</p>
        <Button variante="secundario" onClick={estado.reintentar}>
          Reintentar
        </Button>
      </Card>
    );
  }

  const ejemplo = estado.datos;
  return (
    <Card interactiva={false} className={s.tarjeta}>
      <IlustracionDepa className={s.ilustracion} />
      <div className={s.cuerpo}>
        <h3 className="t-h3">{ejemplo.titulo}</h3>
        <p className={s.precio}>
          <span className="t-h3">{formatMXN(ejemplo.precio_mxn)}</span>
          {ejemplo.operacion === "renta" && <span className={`${s.unidad} t-small`}> al mes</span>}
        </p>
        <ul className={s.chips}>
          {ejemplo.chips.map((c) => (
            <li key={c.texto}>
              <Chip variante={c.variante}>{c.texto}</Chip>
            </li>
          ))}
        </ul>
        <p className={s.comunidad}>{ejemplo.datoComunidad.texto}</p>
        <p className={`${s.fuente} t-small`}>Fuente: {ejemplo.datoComunidad.fuente}</p>
      </div>
    </Card>
  );
}
