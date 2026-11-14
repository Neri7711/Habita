import { useTituloPagina } from "../../app/useTituloPagina";
import { Arranque } from "../../sections/Arranque";

/** Vista tipo app: Arranque trae su propio encabezado (pill + h1), sin EncabezadoPagina para no duplicar títulos. */
export function Buscar() {
  useTituloPagina("Buscar con Habita");
  return <Arranque />;
}
