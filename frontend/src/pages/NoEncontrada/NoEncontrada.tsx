import { useTituloPagina } from "../../app/useTituloPagina";
import { XoloScene } from "../../illustrations";
import { RUTAS } from "../../rutas";
import { Button } from "../../ui";
import s from "./NoEncontrada.module.css";

export function NoEncontrada() {
  useTituloPagina("Página no encontrada");
  return (
    <section className={`contenedor ${s.raiz}`}>
      <XoloScene escena="sentado" alt="" className={s.xolo} />
      <h1 className={`t-h1 ${s.titulo}`}>Esta página se mudó o no existe</h1>
      <p className={`t-body-lg ${s.texto}`}>
        Pasa hasta en las mejores colonias. Vuelve al inicio o cuéntale a Habita qué buscas.
      </p>
      <div className={s.acciones}>
        <Button variante="primario" to={RUTAS.inicio} flecha>
          Volver al inicio
        </Button>
        <Button variante="secundario" to={RUTAS.buscar}>
          Buscar con Habita
        </Button>
      </div>
    </section>
  );
}
