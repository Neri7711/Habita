import type { RouteObject } from "react-router-dom";
import { Buscar } from "../pages/Buscar";
import { Colonias } from "../pages/Colonias";
import { ComoFunciona } from "../pages/ComoFunciona";
import { Inicio } from "../pages/Inicio";
import { NoEncontrada } from "../pages/NoEncontrada";
import { Preguntas } from "../pages/Preguntas";
import { RUTAS } from "../rutas";
import { Layout } from "./Layout";

export const rutasApp: RouteObject[] = [
  {
    element: <Layout />,
    children: [
      { path: RUTAS.inicio, element: <Inicio /> },
      { path: RUTAS.comoFunciona, element: <ComoFunciona /> },
      { path: RUTAS.colonias, element: <Colonias /> },
      { path: RUTAS.preguntas, element: <Preguntas /> },
      { path: RUTAS.buscar, element: <Buscar /> },
      { path: "*", element: <NoEncontrada /> },
    ],
  },
];
