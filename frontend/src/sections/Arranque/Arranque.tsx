import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { ChatPanel } from "../../chat/ChatPanel";
import {
  validarPerfilRapido,
  type CampoFormulario,
  type EntradaFormulario,
  type PerfilRapido,
} from "../../domain";
import { XoloScene } from "../../illustrations";
import { Button, Input, Pill, Toggle } from "../../ui";
import s from "./Arranque.module.css";

type Errores = Partial<Record<CampoFormulario, string>>;
type Mascotas = "si" | "no" | "";

const ORDEN_CAMPOS: CampoFormulario[] = ["operacion", "presupuesto", "destino", "mascotas"];
const OPERACIONES = [
  { valor: "renta", etiqueta: "Rentar" },
  { valor: "compra", etiqueta: "Comprar" },
] as const;
const OPCIONES_MASCOTAS: { valor: Mascotas; etiqueta: string }[] = [
  { valor: "si", etiqueta: "Sí" },
  { valor: "no", etiqueta: "No" },
];

export function Arranque() {
  const [operacion, setOperacion] = useState<PerfilRapido["operacion"]>("renta");
  const [presupuesto, setPresupuesto] = useState("");
  const [destino, setDestino] = useState("");
  const [mascotas, setMascotas] = useState<Mascotas>("");
  const [errores, setErrores] = useState<Errores>({});
  const [perfil, setPerfil] = useState<PerfilRapido | null>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const regresoRef = useRef(false);
  const mascotasErrorId = useId();

  // Al volver del chat, el foco regresa al primer control del formulario.
  useEffect(() => {
    if (perfil === null && regresoRef.current) {
      regresoRef.current = false;
      formRef.current?.querySelector<HTMLElement>("button, input")?.focus();
    }
  }, [perfil]);

  function enfocar(campo: CampoFormulario) {
    const sel = `[data-campo="${campo}"]`;
    formRef.current?.querySelector<HTMLElement>(`${sel} input, ${sel} button`)?.focus();
  }

  function enviar(e: FormEvent) {
    e.preventDefault();
    const entrada: EntradaFormulario = {
      operacion,
      presupuesto,
      destino,
      mascotas: mascotas === "" ? null : mascotas === "si",
    };
    const resultado = validarPerfilRapido(entrada);
    if (!resultado.ok) {
      setErrores(resultado.errores);
      const primero = ORDEN_CAMPOS.find((c) => resultado.errores[c]);
      if (primero) enfocar(primero);
      return;
    }
    setErrores({});
    setPerfil(resultado.perfil);
  }

  function editar() {
    regresoRef.current = true;
    setPerfil(null);
  }

  return (
    <section aria-labelledby="buscar-titulo" className={`contenedor ${s.vista} ${perfil ? s.conChat : ""}`}>
      <div className={s.intro}>
        <Pill punto>Buscar</Pill>
        <h1 id="buscar-titulo" className="t-h1">
          Cuéntale a Habita qué buscas
        </h1>
        <p className={`t-body-lg ${s.lead}`}>
          Cuatro datos y te muestro opciones explicadas: precio justo, confianza del anuncio y cómo es la colonia.
        </p>
        <XoloScene escena="sentado" alt="" className={s.xolo} />
      </div>

      <div className={s.panel}>
        {perfil ? (
          <ChatPanel perfil={perfil} onEditar={editar} />
        ) : (
          <form ref={formRef} className={s.form} onSubmit={enviar} noValidate>
            <div data-campo="operacion" className={s.campo}>
              <span className={s.etiqueta} aria-hidden="true">¿Rentar o comprar?</span>
              <Toggle etiqueta="¿Rentar o comprar?" opciones={OPERACIONES} valor={operacion} onChange={setOperacion} />
            </div>

            <div data-campo="presupuesto">
              <Input
                etiqueta={operacion === "renta" ? "Presupuesto máximo al mes (MXN)" : "Presupuesto máximo (MXN)"}
                inputMode="numeric"
                autoComplete="off"
                placeholder={operacion === "renta" ? "15,000" : "3,500,000"}
                value={presupuesto}
                onChange={(e) => setPresupuesto(e.target.value)}
                error={errores.presupuesto}
              />
            </div>

            <div data-campo="destino">
              <Input
                etiqueta="¿Dónde trabajas?"
                autoComplete="off"
                placeholder="Ej. Reforma, Santa Fe, Polanco"
                value={destino}
                onChange={(e) => setDestino(e.target.value)}
                error={errores.destino}
              />
            </div>

            <fieldset
              data-campo="mascotas"
              className={s.campo}
              aria-describedby={errores.mascotas ? mascotasErrorId : undefined}
            >
              <legend className={s.etiqueta}>¿Tienes mascotas?</legend>
              <Toggle etiqueta="¿Tienes mascotas?" opciones={OPCIONES_MASCOTAS} valor={mascotas} onChange={setMascotas} />
              {errores.mascotas && (
                <p id={mascotasErrorId} className={s.error} role="alert">
                  {errores.mascotas}
                </p>
              )}
            </fieldset>

            <Button type="submit" variante="primario" flecha className={s.enviar}>
              Buscar opciones
            </Button>
          </form>
        )}
      </div>
    </section>
  );
}
