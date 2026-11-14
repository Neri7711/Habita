import { useTituloPagina } from "../../app/useTituloPagina";
import { ComoFunciona as Pasos } from "../../sections/ComoFunciona";
import { EjemploRecomendacion } from "../../sections/EjemploRecomendacion";
import { Pilares } from "../../sections/Pilares";
import { EncabezadoPagina } from "../../ui";

export function ComoFunciona() {
  useTituloPagina("Cómo funciona");
  return (
    <>
      <EncabezadoPagina
        pill="CÓMO FUNCIONA"
        titulo="Así te ayudamos a elegir dónde vivir"
        bajada="Tres pasos, cinco cosas que revisamos por ti y un ejemplo de cómo se ve una recomendación."
      />
      <div className="banda-paper">
        <Pasos />
      </div>
      <div className="banda-surface">
        <Pilares />
      </div>
      {/* Banda paper: la burbuja del usuario usa surface y la respuesta/tarjeta llevan borde line. */}
      <div className="banda-paper">
        <EjemploRecomendacion />
      </div>
    </>
  );
}
