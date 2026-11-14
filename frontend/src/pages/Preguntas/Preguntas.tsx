import { useTituloPagina } from "../../app/useTituloPagina";
import { Faq } from "../../sections/Faq";
import { EncabezadoPagina } from "../../ui";

export function Preguntas() {
  useTituloPagina("Preguntas");
  return (
    <>
      <EncabezadoPagina
        pill="PREGUNTAS"
        titulo="Lo que nos preguntan antes de empezar"
        bajada="Cómo funciona Habita, de dónde salen los datos y qué no hacemos."
      />
      <Faq />
    </>
  );
}
