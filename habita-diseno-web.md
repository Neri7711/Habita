# Habita — Diseño de la landing

Guía visual de la web de Habita, basada en el layout de **CraftHouse — Bespoke Living Spaces** (Dribbble, Shuvo Cold) y adaptada a nuestra marca: tezontle, Xolo 2D facetado e islas isométricas de CDMX.

> Este documento cubre solo lo visual: estructura, componentes, tokens y uso de ilustración. El comportamiento del agente y los datos van en las specs técnicas.

---

## 1. Qué tomamos de CraftHouse

| CraftHouse | En Habita |
| --- | --- |
| Fondo gris claro, mucho aire, editorial y premium | Igual: `surface` #EEEFF0 con secciones separadas por 96px |
| Un solo acento cálido (#A55338) | **Tezontle** #A8452B, la piedra roja del Centro |
| Titular grande con **una palabra en bloque de color** | "**Encuentra** tu lugar en la CDMX sin adivinar" |
| Hero con foto de casa dentro de un contenedor redondeado | Hero con **islas isométricas** de colonias + el Xolo |
| Pills chiquitas como etiqueta de cada sección | Pills tezontle-soft: "CÓMO FUNCIONA", "COLONIAS"... |
| Stats grandes (15+, 120+, 98%) | 15 colonias · 500 anuncios revisados · 100% explicado |
| Grid de cards de servicios con foto | Cards de los 5 pilares (costo real, precio justo...) |
| Testimonio / "Endorsed by" | Ejemplo de recomendación del agente (mock de chat) |
| FAQ en acordeón a dos columnas | FAQ igual |
| CTA final en bloque oscuro con imagen | Bloque `ink` con el Xolo y botón tezontle |
| Formulario de contacto al pie | Arranque del chat: "Cuéntale a Habita qué buscas" |

**Lo que NO copiamos:** las fotos de interiores de lujo. Habita no vende casas; habla de colonias, costos y comunidad. La foto se cambia por ilustración.

---

## 2. Tokens

### Color

| Token | Hex | Uso |
| --- | --- | --- |
| `surface` | #EEEFF0 | Fondo de página |
| `paper` | #F7F6F3 | Cards, inputs |
| `ink` | #131416 | Texto principal, secciones oscuras |
| `ink-muted` | #5C5B57 | Texto secundario |
| `on-ink` | #F7F6F3 | Texto sobre ink / tezontle |
| `line` | #D9D7D2 | Bordes y divisores |
| `tezontle` | #A8452B | Botón primario, palabra resaltada, grecas del Xolo |
| `tezontle-bright` | #D7643F | Acentos sobre fondo ink |
| `tezontle-soft` | #F2D3C4 | Fondo de pills |
| `tezontle-ink` | #8A3720 | Texto de pills |
| `xolo` | #3F444C | Cuerpo de la mascota |
| `sol` | #F2C14E | Fondo de ilustración del Xolo (pose base) |
| `durazno` | #EDB98A | Fondo de escenas del Xolo (onboarding) |
| `cielo` | #8DB4F0 | Cielo de las islas |
| `jacaranda` | #9C7BD8 | Acento del agente IA |

Regla: **neutro primero**. Tezontle máximo en un botón primario por vista, la palabra resaltada del hero y las pills.

### Tipografía

- **Display:** Bricolage Grotesque 800 / 600
- **Texto:** Inter 400 / 500 / 600

| Estilo | Tamaño / interlínea | Peso |
| --- | --- | --- |
| hero | 72 / 76 (móvil 44 / 48) | 800 |
| h1 | 48 / 52 | 800 |
| h2 | 36 / 40 | 600 |
| h3 | 24 / 30 | 600 |
| stat | 44 / 48 | 800 |
| body-lg | 18 / 28 | 400 |
| body | 16 / 24 | 400 |
| small | 14 / 20 | 400 |
| label (pills) | 12 / 16, MAYÚSCULAS, tracking +0.06em | 600 |

Tracking de titulares: −0.02em.

### Espaciado y radios

- Escala: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 96
- Contenedor: máximo 1200px, padding lateral 48px (móvil 20px)
- Entre secciones: 96px (móvil 64px)
- Radios: `sm` 8px (inputs, palabra resaltada) · `md` 16px (cards) · `lg` 28px (hero, bloques grandes) · `pill` 999px (botones, pills)
- Sin sombras pesadas. Si hace falta separar, borde de 1px `line`.

---

## 3. Mapa del sitio y secciones

El sitio es **multipágina** (React Router). Navbar y Footer son comunes a todas las páginas. Las secciones 3.2–3.9 son bloques que se componen por página:

| Ruta | Página | Bloques |
|---|---|---|
| `/` | Inicio | Hero (3.2) · Sobre + stats (3.3) · Pilares en resumen: 3 cards + "Ver los 5 →" (3.4) · Banda oscura (3.7) |
| `/como-funciona` | Cómo funciona | Encabezado de página · Pasos (3.5) · Pilares completos (3.4) · Ejemplo de recomendación (3.6) |
| `/colonias` | Colonias | Encabezado de página · Las 13 colonias piloto agrupadas por alcaldía. **La hipótesis de presión del CSV no se muestra**: "Presión de gentrificación: próximamente" hasta que exista el indicador real (spec 02) |
| `/preguntas` | Preguntas | Encabezado de página · FAQ (3.8) |
| `/buscar` | Buscar con Habita | Arranque del chat (3.9) a pantalla completa, vista tipo app |
| `*` | No encontrada | Xolo + "Esta página se mudó o no existe" + botón a Inicio |

Reglas de ritmo (inspiración CraftHouse):
- Las secciones alternan fondo a todo el ancho: `surface` / `paper`. El contenido sigue en el contenedor de 1200px.
- Las páginas internas abren con un **encabezado de página**: pill + h1 + bajada `body-lg`, 64px arriba / 48px abajo.
- Todos los CTA "Hablar con Habita" / "Empezar mi búsqueda" llevan a `/buscar`. Un solo botón primario tezontle por vista.
- Cada página tiene su `<title>` ("Cómo funciona · Habita") y al navegar el foco va al h1.

Ilustraciones finales: `frontend/src/assets/ilustraciones/*.svg` (fondos ya iguales a los tokens). Se usan como `<img>`, nunca inline.
El hero usa `hero-islas-cdmx.svg` a todo el ancho del contenedor; el bloque se extiende hacia arriba con `cielo` para que el titular quede sobre cielo liso y las islas abajo.

### 3.1 Navbar
- Altura 72px, transparente sobre el hero y `paper` con borde inferior al hacer scroll.
- Izquierda: logo casita-xolo + "habita". Centro: Cómo funciona · Colonias · Preguntas. Derecha: botón pill `ink` "Hablar con Habita".

### 3.2 Hero
- Contenedor `radius-lg` a todo el ancho del contenedor, alto ~640px, fondo `cielo` con las **islas isométricas** (Centro, Roma–Condesa, Coyoacán).
- Texto a la izquierda, sobre un degradado sutil o un área libre del cielo:
  - Titular hero: "[**Encuentra**] tu lugar en la CDMX sin adivinar". La palabra va en un bloque `tezontle` con `radius-sm`, padding 0 12px y texto `on-ink`.
  - Bajada body-lg en `ink`: "Te decimos cuánto cuesta vivir de verdad, si el precio es justo y si el anuncio es confiable."
  - Botón primario pill tezontle "Empezar mi búsqueda →" + botón secundario de texto "Ver cómo funciona".
- Abajo a la derecha, card flotante tipo CraftHouse (la del video): `paper`, `radius-md`, el Xolo en miniatura + "15 colonias piloto · Datos Abiertos CDMX".
- Etiquetas de colonia como pills blancas encima de cada isla (HTML, no dentro del SVG).

### 3.3 Sobre Habita + stats
- Dos columnas. Izquierda: pill "SOBRE HABITA", h2 "Un asesor que solo recomienda", párrafo corto ("No publicamos inmuebles, no cobramos comisión, no contactamos caseros").
- Derecha: ilustración del **Xolo recostado** (pose base) sobre fondo `sol` en un bloque `radius-lg`.
- Fila de 3 stats debajo del texto: número en `stat` + etiqueta `small` en `ink-muted`.

### 3.4 Los 5 pilares (equivalente a "Residential Spaces Through Design")
- Pill "QUÉ TE EXPLICAMOS" + h2 + link "Ver ejemplo →" alineado a la derecha.
- Grid de cards (3 arriba, 2 abajo; móvil 1 columna). Cada card: `paper`, `radius-md`, borde `line`, padding 24px.
  1. **Costo real de vivir**: renta + transporte + tiempo.
  2. **Precio justo**: comparado con la colonia.
  3. **Confianza del anuncio**: señales de fraude en lenguaje simple.
  4. **Encaje con la comunidad**: mercados, parques, cultura.
  5. **Reubicación consciente**: aviso de presión de gentrificación.
- Arriba de cada card, una mini ilustración o un ícono del set facetado. Como alternativa, una greca tezontle distinta por card.

### 3.5 Cómo funciona (onboarding en 3 pasos)
- Pill "CÓMO FUNCIONA". Tres columnas al estilo de las pantallas de Angelic: cada paso tiene una **escena del Xolo** sobre su propio color de fondo, en un bloque `radius-lg`.
  1. *Cuéntanos qué buscas*: Xolo con el mapa (fondo `durazno`).
  2. *Comparamos por ti*: Xolo revisando anuncios (fondo `tezontle-soft`).
  3. *Elige con confianza*: Xolo en la caja de mudanza (fondo `durazno`).
- Título h3 centrado debajo de cada escena + 1 línea `ink-muted`.

### 3.6 Ejemplo de recomendación (equivalente a "Endorsed by")
- Bloque dividido: a la izquierda, mock de chat (burbuja del usuario en `paper`, respuesta del agente con avatar del Xolo y badge "IA" en `jacaranda-soft`).
- A la derecha, la **card de recomendación**: foto o ilustración del depa, precio, chips "Precio justo ✓", "Confianza alta", "32 min a tu trabajo", y un dato de comunidad con su fuente en `small`.

### 3.7 Banda oscura (equivalente a "Ready to Build Your Dream Space?")
- Bloque `ink` con `radius-lg`, ilustración de islas de noche o grecas tezontle-bright de fondo.
- h2 en `on-ink`: "¿Listo para encontrar tu **lugar**?" (la palabra en tezontle-bright) + botón tezontle.

### 3.8 Preguntas frecuentes
- Dos columnas: izquierda, h2 + texto + card pequeña "¿Otra duda? Pregúntale a Habita" con botón. Derecha, acordeón.
- Item del acordeón: fondo `paper`, `radius-md`, 20px de padding, ícono "+" que rota a "×". El item abierto lleva fondo `tezontle-soft` muy sutil.

### 3.9 Arranque del chat (equivalente a "Start Your Transformation")
- Card grande `paper`: a la izquierda, el Xolo sentado + "Cuéntale a Habita qué buscas". A la derecha, un formulario rápido: renta/compra (toggle pill), presupuesto, dónde trabajas, ¿mascotas? Botón "Buscar opciones".

### 3.10 Footer
- Fondo `ink`, logo oscuro, enlaces en `stone`, línea de fuentes de datos ("Datos Abiertos CDMX, INEGI…") y aviso "Habita recomienda; no es asesoría legal ni financiera".

---

## 4. Componentes

**Botón primario**: pill, alto 48px, padding 0 24px, `tezontle` + `on-ink`, Inter 600 15px. Hover: oscurece un 8%. Flecha "→" que se mueve 2px en hover.

**Botón secundario**: pill, borde 1px `ink`, fondo transparente. En fondos ink: borde `on-ink`.

**Pill de sección**: `tezontle-soft` + `tezontle-ink`, label 12px en mayúsculas, padding 6px 12px. Opcional: un punto de 6px tezontle a la izquierda.

**Palabra resaltada**: span con fondo `tezontle`, `radius-sm`, padding 0 .18em, texto `on-ink`. Una por página.

**Card**: `paper`, `radius-md`, borde `line`, padding 24px. Hover: sube 2px y el borde pasa a `ink-muted`.

**Chip de dato**: pill pequeño (28px), fondo `surface`, texto `small` 500. Variantes: confianza (verde suave), alerta (tezontle-soft), IA (jacaranda-soft).

**Stat**: número en Bricolage 800 44px + etiqueta 14px `ink-muted`; separadas por un divisor vertical `line`.

**Input**: alto 48px, `paper`, borde `line`, `radius-sm`; focus: anillo de 2px `tezontle` con 2px de separación.

---

## 5. Ilustración

Hay dos lenguajes, cada uno con su lugar:

**Islas isométricas** (hero y contexto de colonias)
- Isométrico a 30°, luz arriba a la izquierda, caras al 100% / 80% / 125%, sin contorno.
- Una isla por colonia, cada una con sus íconos: Centro (tezontle y torres), Roma–Condesa (art déco y árboles), Coyoacán (casitas de colores y jacarandas).

**El Xolo 2D facetado** (personaje)
- Formas **angulares de corte recto**, sin curvas suaves, como papel recortado.
- Proporciones de xolo real: esbelto, patas largas, orejas grandes triangulares con interior café.
- Cuerpo `xolo` con planos más claros (#4D535C) y más oscuros (#2C3036) para dar volumen sin degradados.
- **Grecas escalonadas (xicalcoliuhqui) en tezontle** sobre el cuerpo y algunas manchas tezontle en la cara.
- Expresión tranquila y medio presumida: ojos entrecerrados y sonrisa de lado.
- Detalles a mano: rayitas cortas tipo lápiz, destellos blancos de 4 puntas y líneas de "movimiento".
- **Grano de papel** encima de toda la ilustración (ruido al ~35%).
- Siempre sobre un **fondo sólido de color** (`sol`, `durazno`, `tezontle-soft`), nunca recortado sobre blanco ni sobre fotos.
- Escenas planeadas: recostado (base) · en la caja de mudanza · con el mapa · revisando anuncios en la laptop · con llaves en la boca · dormido (estado vacío).

---

## 6. Responsive

- **≥1200px:** layout descrito arriba.
- **768–1199px:** grids de 3 columnas pasan a 2; el hero apila texto arriba e islas abajo.
- **<768px:** todo a 1 columna, hero 44px, secciones a 64px, navbar con menú hamburguesa y botón "Hablar" fijo abajo como pill flotante.

## 7. Movimiento

- Entrada de secciones: fade + 16px hacia arriba, 400ms, ease-out, escalonado de 60ms.
- Las islas del hero flotan con un leve bobbing (±6px, 6s, desfasadas entre sí).
- Los destellos del Xolo parpadean suave (opacidad .4 → 1, 2.4s).
- Respetar `prefers-reduced-motion`: sin bobbing ni parpadeo.

## 8. Accesibilidad

- `ink` sobre `surface` 16:1 · `ink-muted` sobre `surface` 5.9:1 · `on-ink` sobre `tezontle` 5.5:1 · `tezontle-ink` sobre `tezontle-soft` 5.6:1.
- Las ilustraciones son decorativas (`alt=""`), salvo las escenas de "Cómo funciona", que llevan alt descriptivo.
- Foco visible en todos los controles (anillo tezontle).
