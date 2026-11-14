import { useEffect, useRef, useState, type ReactNode } from "react";
import { useClient } from "../client/useClient";
import { mensajeDeError } from "../client/ErrorApi";
import { nombreZona, type OpcionBusqueda, type PerfilRapido } from "../domain";
import { XoloScene } from "../illustrations";
import { formatMXN } from "../lib/format";
import { Button, Card, Chip } from "../ui";
import {
  avanzar,
  etiquetaIntencion,
  iniciar,
  type CierreResultados,
  type EstadoChat,
  type Intencion,
  type Mensaje,
} from "./scriptedChat";
import s from "./ChatPanel.module.css";

type ChatPanelProps = { perfil: PerfilRapido; onEditar: () => void };

type Vista =
  | { tipo: "cargando" }
  | { tipo: "error"; mensaje: string }
  | { tipo: "listo"; estado: EstadoChat; mensajes: Mensaje[] };

/** Primer mensaje del usuario: resume lo que capturó en el formulario. */
function resumenPerfil(p: PerfilRapido): Mensaje {
  const operacion = p.operacion === "renta" ? "rentar" : "comprar";
  const mascotas = p.mascotas ? "con mascotas" : "sin mascotas";
  return {
    id: "perfil",
    autor: "usuario",
    texto: `Quiero ${operacion} con un presupuesto de hasta ${formatMXN(p.presupuesto_max_mxn)}. Trabajo en ${nombreZona(p.destino_trabajo)}, ${mascotas}.`,
  };
}

export function ChatPanel({ perfil, onEditar }: ChatPanelProps) {
  const client = useClient();
  const [vista, setVista] = useState<Vista>({ tipo: "cargando" });
  const [intento, setIntento] = useState(0);
  const tituloRef = useRef<HTMLHeadingElement>(null);
  const mensajesRef = useRef<HTMLDivElement>(null);
  const previosRef = useRef(0);

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
      (error) => vigente && setVista({ tipo: "error", mensaje: mensajeDeError(error) }),
    );
    return () => {
      vigente = false;
    };
  }, [client, perfil, intento]);

  // En escritorio los mensajes tienen scroll propio: lleva a la vista el primer mensaje nuevo.
  const total = vista.tipo === "listo" ? vista.mensajes.length : 0;
  useEffect(() => {
    const el = mensajesRef.current;
    const nuevo = el?.children[previosRef.current] as HTMLElement | undefined;
    previosRef.current = total;
    if (!el || !nuevo || el.scrollHeight <= el.clientHeight) return;
    el.scrollTop = nuevo.offsetTop;
  }, [total]);

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

      <div
        ref={mensajesRef}
        className={s.mensajes}
        role="log"
        aria-label="Conversación con Habita"
        aria-busy={vista.tipo === "cargando"}
        tabIndex={0}
      >
        {vista.tipo === "cargando" && (
          <BurbujaAgente>
            <p className={s.cargando}>Buscando opciones de ejemplo para ti…</p>
          </BurbujaAgente>
        )}

        {vista.tipo === "error" && (
          <BurbujaAgente>
            <p>{vista.mensaje}</p>
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
                {m.supuestos && m.supuestos.length > 0 && <Supuestos items={m.supuestos} />}
                {m.tarjeta && <TarjetaOpcion opcion={m.tarjeta} />}
                {m.cierre && <Cierre cierre={m.cierre} />}
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

/** El back puede repetir avisos (costo real y precio justo traen los mismos); se muestran una vez. */
const unicos = (xs: string[]) => [...new Set(xs)];

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

function Supuestos({ items }: { items: string[] }) {
  return (
    <div className={s.supuestos}>
      <p className={s.supuestosTitulo}>Asumimos que…</p>
      <ul>
        {items.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

function Cierre({ cierre }: { cierre: CierreResultados }) {
  const { avisos, fuentes, alternativas } = cierre;
  return (
    <div className={s.cierre}>
      {avisos.length > 0 && (
        <ul className={s.avisos}>
          {unicos(avisos).map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
      {alternativas && <p>{alternativas}</p>}
      {fuentes.length > 0 && (
        <ul className={s.fuentes} aria-label="Fuentes">
          {fuentes.map((f) => (
            <li key={f.descripcion}>
              Fuente: {f.descripcion}
              {f.fecha_dato ? ` (${f.fecha_dato})` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TarjetaOpcion({ opcion }: { opcion: OpcionBusqueda }) {
  const precio = formatMXN(opcion.precio_mxn) + (opcion.operacion === "renta" ? " / mes" : "");
  return (
    <Card interactiva={false} className={s.tarjeta}>
      <h3 className={s.tarjetaTitulo}>{opcion.titulo}</h3>
      <p className={s.tarjetaMeta}>
        {opcion.colonia} · <strong>{precio}</strong>
      </p>
      {opcion.porQue && <p className={s.dato}>{opcion.porQue}</p>}
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
      {opcion.avisos && opcion.avisos.length > 0 && (
        <ul className={s.avisos}>
          {unicos(opcion.avisos).map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}
