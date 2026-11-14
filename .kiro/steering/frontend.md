---
inclusion: fileMatch
fileMatchPattern: "frontend/**"
---

# Frontend Habita

Fuente de verdad visual: `habita-diseno-web.md` (raíz). Diseño técnico: `.kiro/specs/frontend-landing-habita/design.md`.
Contexto de diseño para las skills de diseño: `.impeccable.md` (raíz).
Referencia de composición (no de estilo): `.kiro/specs/frontend-landing-habita/referencias/` (CraftHouse).
Si la referencia y `habita-diseno-web.md` no coinciden, gana el documento.

## Decisiones cerradas (hackatón, prevalecen sobre design.md)
- Nombre en la UI: **Habita**.
- Stack: Vite + React 18 + TypeScript estricto en `frontend/`, CSS con variables (`src/styles/tokens.css`) + CSS Modules. npm.
- Tokens nuevos aceptados: `stone` #B9B6AE, `jacaranda-soft` #E6DDF7, más los que propone design.md (verde confianza, cielo de noche).
- **Sitio multipágina** con `react-router-dom` (mapa del sitio en `habita-diseno-web.md` §3). Rutas en `src/rutas.ts`; nunca escribir rutas a mano en los componentes.
  Esto reemplaza la decisión de design.md de "una sola página con anclas".
- Ilustraciones finales en `src/assets/ilustraciones/*.svg`, usadas como `<img>` (el grano es un filtro SVG costoso; como img se rasteriza una vez). NO construir `IsleScene` ni `lib/iso.ts`.
  Escenas sin ilustración (llaves, dormido): `Placeholder`.
- Colonias: el conteo sale de los datos (13). Nunca escribir "15" a mano. Anuncios: 300 sintéticos (dato del back), sigue marcado como provisional en el mock.
- `hipotesis_presion` y `rol` del CSV son hipótesis del equipo: **no se muestran en la UI**.
- Pruebas: Vitest + Testing Library solo para lo que tiene lógica (máquina del chat guionado, validación del formulario, `buscarOpciones`). **Sin fast-check ni pruebas de propiedades.**
- Sin LLM, sin claves, sin llamadas de red en el front. Todo dato pasa por `HabitaClient` (mock).
- Sin plugins de imagen.

## Reglas de trabajo en paralelo
- Cada carril solo toca SUS archivos (ver `.kiro/orquestacion/carriles-front.md`). Si necesitas algo de otro carril, impórtalo; si no existe, avisa en vez de crearlo.
- Nadie hace commit ni push.
- Nada sobre-ingenierizado: el código más simple que cumpla el documento.
