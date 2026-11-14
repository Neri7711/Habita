import { useTituloPagina } from "../../app/useTituloPagina";
import { BandaOscura } from "../../sections/BandaOscura";
import { Hero } from "../../sections/Hero";
import { Pilares } from "../../sections/Pilares";
import { Sobre } from "../../sections/Sobre";
import s from "./Inicio.module.css";

/** Ritmo §3: Hero → Sobre (paper) → Pilares en resumen + cierre oscuro (surface). */
export function Inicio() {
  useTituloPagina("Inicio");
  return (
    <>
      <Hero />
      <div className={`banda-paper ${s.banda}`}>
        <Sobre />
      </div>
      <div className={`banda-surface ${s.banda}`}>
        <Pilares resumen />
        <BandaOscura />
      </div>
    </>
  );
}
