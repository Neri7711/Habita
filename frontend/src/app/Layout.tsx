import { Outlet, ScrollRestoration } from "react-router-dom";
import { Footer } from "../sections/Footer";
import { Navbar } from "../sections/Navbar";

export function Layout() {
  return (
    <>
      <Navbar />
      <main>
        <Outlet />
      </main>
      <Footer />
      <ScrollRestoration />
    </>
  );
}
