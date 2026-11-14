import { useEffect, useRef, useState, type ReactNode } from "react";
import { useClient } from "../client/useClient";
import type { PerfilRapido, RecomendacionEjemplo } from "../domain";
import { XoloScene } from "../illustrations";
import { formatMXN } from "../lib/format";
import { Button, Card, Chip } from "../ui";
import { avanzar, etiquetaIntencion, iniciar, type EstadoChat, type Intencion, type Mensaje } from "./scriptedChat";
import s from "./ChatPanel.module.css";

type ChatPanelProps = { perfil: PerfilRapido; onEditar: () => void };

type Vista =
  | { tipo: "cargando" }
  | { tipo: "error" }
  | { tipo: "listo"; estado: EstadoChat; mensajes: Mensaje[] };

/** Primer mensaje del usuario: resume lo que capturó en el formulario. */
function resumenPerfil(p: PerfilRapido): Mensaje {
  const operacion = p.operacion === "renta" ? "rentar" : "comprar";
  const mascotas = p.mascotas ? "con mascotas" : "sin mascotas";
  return {
    id: "perfil",
    autor: "usuario",
    texto: `Quiero ${operacion} con un presupuesto de hasta ${formatMXN(p.presupuesto_max_mxn)}. Trabajo en ${p.destino_trabajo}, ${mascotas}.`,
  };
}

export function ChatPanel({ perfil, onEditar }: ChatPanelProps) {
  const client = useClient();
  const [vista, setVista] = useState<Vista>({ tipo: "cargando" });
  const [intento, setIntento] = useState(0);
  const tituloRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    tituloRef.current?.focus();
  }, []);

  useEffect(() => {
    let vigente = true;
    setVista({ tipo: "cargando" });
    client.buscarOpciones(perfil).then(
      (resultado) => {
        if (!vigente) return;
        const paso = iniciar(perfil, resultado);
        setVista({ tipo: "listo", estado: paso.estado, mensajes: [resumenPerfil(perfil), ...paso.mensajes] });
      },
      () => vigente && setVista({ tipo: "error" }),
    );
    return () => {
      vigente = false;
    };
  }, [client, perfil, intento]);

  function elegir(intencion: Intencion) {
    // "Cambiar mi búsqueda" regresa al formulario con los valores previos.
    if (intencion.tipo === "reiniciar") return onEditar();
    if (vista.tipo !== "listo") return;
    const paso = avanzar(vista.estado, intencion);
    setVista({ tipo: "listo", estado: paso.estado, mensajes: [...vista.mensajes, ...paso.mensajes] });
  }

  const ultimo = vista.tipo === "listo" ? vista.mensajes[vista.mensajes.length - 1] : undefined;
  const sugerencias = ultimo?.autor === "agente" ? ultimo.sugerencias ?? [] : [];

  return (
    <div className={s.panel}>
      <header className={s.cabecera}>
        <h2 ref={tituloRef} tabIndex={-1} className={`t-h3 ${s.titulo}`}>
          Tu búsqueda con Habita
        </h2>
        {client.origen === "mock" && <Chip variante="neutro">Datos de ejemplo</Chip>}
      </header>

      <div className={s.mensajes} aria-live="polite" aria-busy={vista.tipo === "cargando"}>
        {vista.tipo === "cargando" && (
          <BurbujaAgente>
            <p className={s.cargando}>Buscando opciones de ejemplo para ti…</p>
          </BurbujaAgente>
        )}

        {vista.tipo === "error" && (
          <BurbujaAgente>
            <p>Uy, no pude traer las opciones en este momento. No es tu culpa; inténtalo de nuevo o ajusta tu búsqueda.</p>
            <div className={s.acciones}>
              <button type="button" className={s.sugerencia} onClick={() => setIntento((n) => n + 1)}>
                Reintentar
              </button>
            </div>
          </BurbujaAgente>
        )}

        {vista.tipo === "listo" &&
          vista.mensajes.map((m) =>
            m.autor === "usuario" ? (
              <div key={m.id} className={s.usuario}>
                <p className={s.burbujaUsuario}>{m.texto}</p>
              </div>
            ) : (
              <BurbujaAgente key={m.id}>
                <p>{m.texto}</p>
                {m.tarjeta && <TarjetaOpcion opcion={m.tarjeta} />}
              </BurbujaAgente>
            ),
          )}
      </div>

      {sugerencias.length > 0 && (
        <div className={s.acciones} role="group" aria-label="Sugerencias">
          {sugerencias.map((i) => (
            <button key={etiquetaIntencion(i)} type="button" className={s.sugerencia} onClick={() => elegir(i)}>
              {etiquetaIntencion(i)}
            </button>
          ))}
        </div>
      )}

      <div className={s.pie}>
        <Button variante="secundario" onClick={onEditar}>
          Editar mi búsqueda
        </Button>
      </div>
    </div>
  );
}

function BurbujaAgente({ children }: { children: ReactNode }) {
  return (
    <div className={s.agente}>
      <XoloScene escena="recostado" alt="" className={s.avatar} />
      <div className={s.cuerpoAgente}>
        <p className={s.autor}>
          Habita <Chip variante="ia">IA</Chip>
        </p>
        {children}
      </div>
    </div>
  );
}

function TarjetaOpcion({ opcion }: { opcion: RecomendacionEjemplo }) {
  const precio = formatMXN(opcion.precio_mxn) + (opcion.operacion === "renta" ? " / mes" : "");
  return (
    <Card interactiva={false} className={s.tarjeta}>
      <h3 className={s.tarjetaTitulo}>{opcion.titulo}</h3>
      <p className={s.tarjetaMeta}>
        {opcion.colonia} · <strong>{precio}</strong>
      </p>
      <ul className={s.chips}>
        {opcion.chips.map((c) => (
          <li key={c.texto}>
            <Chip variante={c.variante}>{c.texto}</Chip>
          </li>
        ))}
      </ul>
      <p className={s.dato}>
        {opcion.datoComunidad.texto}{" "}
        <span className={s.fuente}>
          Fuente: {opcion.datoComunidad.fuente} ({opcion.datoComunidad.fecha_dato})
        </span>
      </p>
    </Card>
  );
}
