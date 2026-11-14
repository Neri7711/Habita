import type { ColoniaResumen } from "../domain";

// Copia de data/raw/colonias_piloto.csv (13 filas). El conteo de colonias sale de aquí.
export const COLONIAS: ColoniaResumen[] = [
  { colonia: "Roma Norte", alcaldia: "Cuauhtémoc", hipotesis_presion: "alta", rol: "zona_presionada" },
  { colonia: "Hipódromo", alcaldia: "Cuauhtémoc", hipotesis_presion: "alta", rol: "zona_presionada" },
  { colonia: "Juárez", alcaldia: "Cuauhtémoc", hipotesis_presion: "alta", rol: "zona_presionada" },
  { colonia: "Escandón I Sección", alcaldia: "Miguel Hidalgo", hipotesis_presion: "alta", rol: "zona_presionada" },
  { colonia: "San Rafael", alcaldia: "Cuauhtémoc", hipotesis_presion: "media", rol: "en_transicion" },
  { colonia: "Santa María la Ribera", alcaldia: "Cuauhtémoc", hipotesis_presion: "media", rol: "en_transicion" },
  { colonia: "Tacubaya", alcaldia: "Miguel Hidalgo", hipotesis_presion: "media", rol: "en_transicion" },
  { colonia: "Narvarte Poniente", alcaldia: "Benito Juárez", hipotesis_presion: "media", rol: "alternativa" },
  { colonia: "Del Valle Centro", alcaldia: "Benito Juárez", hipotesis_presion: "media", rol: "alternativa" },
  { colonia: "Portales Norte", alcaldia: "Benito Juárez", hipotesis_presion: "baja", rol: "alternativa" },
  { colonia: "Álamos", alcaldia: "Benito Juárez", hipotesis_presion: "baja", rol: "alternativa" },
  { colonia: "Moctezuma 2a Sección", alcaldia: "Venustiano Carranza", hipotesis_presion: "baja", rol: "alternativa" },
  { colonia: "Lindavista", alcaldia: "Gustavo A. Madero", hipotesis_presion: "baja", rol: "alternativa" },
];
