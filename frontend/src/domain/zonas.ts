import type { ZonaTrabajo } from "./ui";

/**
 * Zonas de trabajo: la misma lista cerrada que expone el back en GET /api/zonas
 * (src/arraigo/api_web.py). La usa el mock y sirve para mostrar el nombre de un id sin pedirlo a la API.
 */
export const ZONAS_TRABAJO: readonly ZonaTrabajo[] = [
  { id: "reforma", nombre: "Paseo de la Reforma", lat: 19.427, lng: -99.1677 },
  { id: "polanco", nombre: "Polanco", lat: 19.433, lng: -99.191 },
  { id: "santa-fe", nombre: "Santa Fe", lat: 19.359, lng: -99.26 },
  { id: "centro", nombre: "Centro Histórico", lat: 19.4326, lng: -99.1332 },
  { id: "insurgentes-sur", nombre: "Insurgentes Sur / Del Valle", lat: 19.387, lng: -99.174 },
  { id: "roma-condesa", nombre: "Roma / Condesa", lat: 19.415, lng: -99.165 },
  { id: "coyoacan", nombre: "Coyoacán", lat: 19.35, lng: -99.162 },
  { id: "periferico-sur", nombre: "Periférico Sur", lat: 19.304, lng: -99.19 },
  { id: "aeropuerto", nombre: "Aeropuerto (AICM)", lat: 19.4361, lng: -99.0719 },
];

/** Nombre legible de una zona; si el id no está en la lista, devuelve el texto tal cual. */
export function nombreZona(id: string): string {
  return ZONAS_TRABAJO.find((z) => z.id === id)?.nombre ?? id;
}
