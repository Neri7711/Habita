import { useEffect, useState } from "react";
import { useClient } from "../../client/useClient";
import type { PreguntaFrecuente } from "../../domain";
import { RUTAS } from "../../rutas";
import { Accordion, Button, Card, Reveal } from "../../ui";
import s from "./Faq.module.css";

type Estado = "cargando" | "error" | PreguntaFrecuente[];

/** Acordeón de preguntas + card de "¿Otra duda?". El h1 lo pone la página (Preguntas). */
export function Faq() {
  const client = useClient();
  const [estado, setEstado] = useState<Estado>("cargando");

  useEffect(() => {
    let vivo = true;
    client
      .listarFaq()
      .then((faq) => vivo && setEstado(faq))
      .catch(() => vivo && setEstado("error"));
    return () => {
      vivo = false;
    };
  }, [client]);

  return (
    <section aria-labelledby="faq-titulo" className={`contenedor ${s.seccion}`}>
      <h2 id="faq-titulo" className="sr-only">
        Preguntas frecuentes
      </h2>
      <div className={s.grid}>
        <div className={s.lateral}>
          <Reveal>
            <Card interactiva={false} className={s.duda}>
              <p className="t-h3">¿Otra duda? Pregúntale a Habita</p>
              <p className={`${s.texto} t-body`}>
                Si algo no queda claro, Habita te lo explica con tus datos: presupuesto, trabajo y mascotas.
              </p>
              <Button variante="secundario" to={RUTAS.buscar} flecha>
                Ir al chat
              </Button>
            </Card>
          </Reveal>
        </div>

        <Reveal retrasoMs={60}>
          {estado === "cargando" && (
            <p className={`${s.texto} t-small`} role="status" aria-busy="true">
              Cargando preguntas…
            </p>
          )}
          {estado === "error" && (
            <p className={`${s.texto} t-small`} role="status">
              No pudimos cargar las preguntas. Intenta recargar la página.
            </p>
          )}
          {Array.isArray(estado) && (
            <Accordion
              items={estado.map((p) => ({ id: p.id, titulo: p.pregunta, contenido: <p>{p.respuesta}</p> }))}
            />
          )}
        </Reveal>
      </div>
    </section>
  );
}
