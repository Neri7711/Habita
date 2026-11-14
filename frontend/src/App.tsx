import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { rutasApp } from "./app/rutasApp";
import { ClientProvider } from "./client/ClientProvider";

const router = createBrowserRouter(rutasApp);

export function App() {
  return (
    <ClientProvider>
      <RouterProvider router={router} />
    </ClientProvider>
  );
}
