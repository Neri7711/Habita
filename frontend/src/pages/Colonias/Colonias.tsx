import { useTituloPagina } from "../../app/useTituloPagina";
import { CierreColonias, ListaColonias, useColonias } from "../../sections/Colonias";
import { EncabezadoPagina } from "../../ui";

export function Colonias() {
  useTituloPagina("Colonias");
  const estado = useColonias();
  const n = Array.isArray(estado) ? `${estado.length} ` : "";

  return (
    <>
      <EncabezadoPagina
        pill="COLONIAS"
        titulo={`Las ${n}colonias piloto`}
        bajada="Son las colonias con datos en esta demo, agrupadas por alcaldía. Aquí empezamos a recomendar; iremos sumando más."
      />
      <ListaColonias estado={estado} />
      <CierreColonias />
    </>
  );
}
