# Carriles del frontend (Habita)

Cada carril = un chat de Kiro distinto sobre este repo. Todos leen primero:
`#steering` (incluye `frontend.md`), `habita-diseno-web.md`, `.kiro/specs/frontend-landing-habita/design.md` y `.impeccable.md`.
Las decisiones de `.kiro/steering/frontend.md` prevalecen sobre `design.md` (sin IsleScene procedural, sin fast-check).

Reglas: solo tocas TUS archivos. Nadie hace commit. Al terminar, crea el archivo marcador indicado (vacío) y resume lo hecho.
Skills disponibles: usa `impeccable` para construir; `full-output-enforcement` en archivos largos; `ponytail` para no sobre-ingenierizar.

Oleadas:
- **Oleada 1 (en paralelo):** F0 y F1.
- **Oleada 2 (en paralelo, cuando existan F0.listo y F1.listo):** S1, S2, S3, S4.
- **Oleada 3:** revisión con skills (Claude Code): audit, adapt, animate, polish, web-design-guidelines, ponytail-review.

Marcadores: `.kiro/orquestacion/front/<CARRIL>.listo`

## Anclas de la página (fijas)
| Sección | Componente | id |
|---|---|---|
| 3.1 | Navbar | — |
| 3.2 | Hero | `inicio` |
| 3.3 | Sobre | `colonias` |
| 3.4 | Pilares | `que-explicamos` |
| 3.5 | ComoFunciona | `como-funciona` |
| 3.6 | EjemploRecomendacion | `ejemplo` |
| 3.7 | BandaOscura | — |
| 3.8 | Faq | `preguntas` |
| 3.9 | Arranque | `chat` |
| 3.10 | Footer | — |

---

## F0 — Base del proyecto (oleada 1)
**Archivos:** `frontend/` raíz (`package.json`, `index.html`, `vite.config.ts`, `tsconfig*.json`, `vitest.setup.ts`, `.gitignore`),
`frontend/src/main.tsx`, `App.tsx`, `brand.ts`, `vite-env.d.ts`, `styles/*`, `ui/*`, `hooks/*`, `illustrations/*`, `assets/*`,
y los **stubs** de `sections/*`.
1. Crea el proyecto Vite + React 18 + TS estricto con npm. Dependencias: react, react-dom, @fontsource-variable/bricolage-grotesque,
   @fontsource-variable/inter; dev: vite, @vitejs/plugin-react, typescript, vitest, jsdom, @testing-library/react,
   @testing-library/user-event, @testing-library/jest-dom. Scripts: dev, build, preview, test (`vitest run`), typecheck (`tsc -b --noEmit` o equivalente).
2. `styles/tokens.css` con TODOS los tokens de `habita-diseno-web.md` §2 + los aceptados en `frontend.md`; `base.css` (reset, tipografía, contenedor 1200/48px, foco tezontle); `motion.css` (reveal y `prefers-reduced-motion`).
3. `ui/`: Button, Pill, Chip, Card, Input, Toggle, Accordion, Reveal, Stat (con CSS Modules, props de design.md §"Componentes UI base") y un `ui/index.ts`.
4. `hooks/`: useReveal, useScrolled, useReducedMotion, useMediaQuery.
5. `illustrations/`: XoloScene (usa PNG si existe, si no Placeholder), Placeholder, Greca (variantes A–E en SVG simple).
6. Copia (no muevas) `caja.png`, `pose.png` a `src/assets/xolo/` y `hero-clay.png` a `src/assets/hero/`.
7. `brand.ts` con el nombre "Habita".
8. Stubs: para cada sección de la tabla de anclas crea `src/sections/<Nombre>/<Nombre>.tsx` (+ `.module.css` vacío) que renderice
   `<section id="…">` con el título de la sección. `App.tsx` los importa en orden y envuelve todo en `ClientProvider`
   importado de `../client/ClientProvider` (lo escribe F1; si aún no existe al compilar, espera a que exista, no lo crees).
9. Termina con `npm install`, `npm run typecheck`, `npm run build` en verde. Marcador: `.kiro/orquestacion/front/F0.listo`.

## F1 — Datos, cliente mock y chat guionado (oleada 1)
**Archivos:** `frontend/src/domain/*`, `client/*` (HabitaClient.ts, MockHabitaClient.ts, ClientProvider.tsx, useClient.ts),
`mocks/*`, `chat/scriptedChat.ts`, `lib/format.ts`, y sus pruebas `*.test.ts` junto a cada archivo.
1. Implementa lo de design.md §"Capa de acceso a datos", §"Data Models", §"Chat guionado", §"Filtro del mock buscarOpciones", §"Validación del formulario".
2. Colonias: copia una vez los datos de `data/raw/colonias_piloto.csv` a `mocks/colonias.ts` (sin prueba de sincronización).
3. Todo mock con `fuente: "sintetico"`; `origen: "mock"`. Stat de anuncios = constante `ANUNCIOS_PROVISIONAL` comentada.
4. Pruebas solo de: máquina del chat (todas las transiciones responden), validación del formulario, `buscarOpciones` (operación y presupuesto). Sin fast-check.
5. NO toques `package.json`. Si F0 aún no termina, escribe el código y espera a `.kiro/orquestacion/front/F0.listo` para correr
   `npm run test` y `npm run typecheck`. Marcador: `.kiro/orquestacion/front/F1.listo`.

---

## S1 — Navbar, Hero, Footer (oleada 2)
**Archivos:** `src/sections/Navbar/*`, `src/sections/Hero/*`, `src/sections/Footer/*`.
Según `habita-diseno-web.md` §3.1, §3.2, §3.10 y §6. Hero: `hero-clay.png` como imagen del contenedor `radius-lg` (object-fit cover),
texto a la izquierda con la palabra resaltada "Encuentra", pills HTML de colonia sobre las islas, card flotante con el Xolo
(miniatura de pose.png) y el conteo de colonias desde `useClient().listarColonias()`. Navbar con hamburguesa <768 y pill "Hablar" fija abajo en móvil.
Marcador: `S1.listo` (tras `npm run typecheck`).

## S2 — Sobre, Pilares, Cómo funciona (oleada 2)
**Archivos:** `src/sections/Sobre/*`, `src/sections/Pilares/*`, `src/sections/ComoFunciona/*`.
Según §3.3, §3.4, §3.5. Stats desde `obtenerStats()`. Pilares: 5 cards 3+2 con Greca A–E. Cómo funciona: pasos 1 y 2 con Placeholder
(fondos `durazno` y `tezontle-soft`), paso 3 con `caja.png`. Marcador: `S2.listo`.

## S3 — Ejemplo, Banda oscura, FAQ (oleada 2)
**Archivos:** `src/sections/EjemploRecomendacion/*`, `src/sections/BandaOscura/*`, `src/sections/Faq/*`.
Según §3.6, §3.7, §3.8. Ejemplo desde `obtenerEjemplo()`, con la etiqueta "Datos de ejemplo" si `origen === "mock"`.
FAQ desde `listarFaq()` con el `Accordion` de `ui/`. Marcador: `S3.listo`.

## S4 — Arranque del chat (oleada 2)
**Archivos:** `src/sections/Arranque/*`, `src/chat/ChatPanel.tsx`, `src/chat/ChatPanel.module.css`.
Según §3.9: formulario rápido (renta/compra con Toggle, presupuesto, dónde trabajas, mascotas) validado con la función de F1;
al enviar, el bloque pasa a `ChatPanel`, que usa `chat/scriptedChat.ts` y `buscarOpciones()`. Estados: cargando, sin resultados, error.
Prueba de integración mínima del flujo formulario → chat. Marcador: `S4.listo`.

---

# Ronda 2 — Multipágina (reemplaza la tabla de anclas de arriba)

Mapa del sitio: `habita-diseno-web.md` §3. Marcadores: `.kiro/orquestacion/front/<CARRIL>.listo`.
- **R0 (solo, primero):** router, layout, páginas ensambladas, enlaces, ilustraciones.
- **P1–P4 (en paralelo, cuando exista R0.listo).**
- Después: revisión con skills.

## R0 — Router y estructura
**Archivos:** `package.json` (solo `react-router-dom`), `src/App.tsx`, `src/main.tsx`, `src/rutas.ts`, `src/app/*` (Layout, hooks de título/foco),
`src/pages/*` (ensamblado inicial de todas las páginas), `src/sections/Navbar/*`, `src/sections/Footer/*`, `src/ui/*`, `src/styles/*`,
`src/illustrations/*`, `src/assets/*`, y en las secciones SOLO el cambio de enlaces `#...` → rutas (Hero, Faq, BandaOscura, Pilares).
Incluye: `Button` con navegación interna (Link), `ui/EncabezadoPagina`, clases de banda alterna, `Pilares` con prop `resumen` (3 cards + enlace),
XoloScene con los SVG, Hero apuntando a `hero-islas-cdmx.svg`, borrar PNG que queden sin uso, página 404, prueba de rutas.

## P1 — Inicio
**Archivos:** `src/pages/Inicio/*`, `src/sections/Hero/*`, `src/sections/Sobre/*`, `src/sections/BandaOscura/*`.
Hero a todo el ancho con el SVG nuevo y cielo extendido arriba (ver §3), ritmo de bandas en Inicio.

## P2 — Cómo funciona
**Archivos:** `src/pages/ComoFunciona/*`, `src/sections/ComoFunciona/*`, `src/sections/Pilares/*`, `src/sections/EjemploRecomendacion/*`.

## P3 — Colonias (nueva)
**Archivos:** `src/pages/Colonias/*`, `src/sections/Colonias/*`. Datos con `listarColonias()`. Sin hipótesis de presión.

## P4 — Preguntas, Buscar y 404
**Archivos:** `src/pages/Preguntas/*`, `src/pages/Buscar/*`, `src/pages/NoEncontrada/*`, `src/sections/Faq/*`, `src/sections/Arranque/*`, `src/chat/ChatPanel.*`.
