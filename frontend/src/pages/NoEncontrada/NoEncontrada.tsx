import { useTituloPagina } from "../../app/useTituloPagina";
import { XoloScene } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Button } from "../../ui";
import s from "./NoEncontrada.module.css";

export function NoEncontrada() {
  useTituloPagina("Página no encontrada");
  return (
    <section className={`contenedor seccion ${s.raiz}`}>
      <XoloScene escena="sentado" alt="" className={s.xolo} />
      <h1 className="t-h1">Esta página se mudó o no existe</h1>
      <Button variante="primario" to={RUTAS.inicio} flecha>
        Volver al inicio
      </Button>
    </section>
  );
}
