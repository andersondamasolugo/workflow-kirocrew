---
inclusion: fileMatch
fileMatchPattern: ["**/*.html", "**/*.css", "**/*.scss", "**/*.sass", "tailwind.config.*"]
---

# Reglas HTML y CSS (front moderno)

## HTML semántico
- Elementos por significado, no por apariencia: `header`, `nav`, `main`, `section`, `article`, `footer`, `button`, `dialog`, `details` — `div` solo cuando no exista elemento semántico.
- Un solo `h1` por página; jerarquía de encabezados sin saltos (h1 → h2 → h3).
- `button` para acciones, `a` para navegación; nunca `div onclick`.
- Imágenes con `alt` significativo (o `alt=""` si es decorativa) y `width`/`height` para evitar saltos de layout.
- `loading="lazy"` en imágenes bajo el pliegue; formatos modernos (WebP/AVIF) con `picture` como fallback.

## Accesibilidad (obligatoria, no opcional)
- Todo input con `label` asociado; grupos con `fieldset`/`legend`.
- Contraste mínimo WCAG AA (4.5:1 texto normal); nunca comunicar solo con color.
- Navegable por teclado: foco visible, orden lógico, sin `tabindex` positivos.
- ARIA solo cuando el HTML semántico no alcanza; el primer recurso es el elemento correcto.
- `prefers-reduced-motion` respetado en animaciones.

## CSS: arquitectura
- Variables CSS (`--color-primary`, `--space-4`) para colores, espaciados y tipografía — un solo lugar para el tema (y soporte de modo oscuro con `color-scheme`).
- Convención de nombres consistente: BEM (`card__title--active`) o utilidades (Tailwind); no mezclar estilos de arquitectura en el mismo proyecto.
- Especificidad baja y plana: clases, no selectores anidados profundos ni `#id`; `!important` prohibido salvo utilidades documentadas.
- Estilos por componente junto al componente (CSS Modules / scoped / capa de utilidades); nada de hojas globales gigantes salvo reset y tokens.

## Layout moderno
- Flexbox para distribución en un eje; Grid para layouts bidimensionales — no floats ni tablas para layout.
- `gap` para espaciado entre hijos en lugar de márgenes acoplados.
- Unidades relativas: `rem` para tipografía/espaciado, `%`/`fr`/`minmax()` para layout; `px` solo para bordes y detalles finos.
- Responsive mobile-first: estilos base para móvil + `min-width` media queries; container queries para componentes reutilizables.
- `aspect-ratio`, `clamp()` para tipografía fluida, `object-fit` para medios.

## Rendimiento
- CSS crítico pequeño; evitar frameworks completos para usar el 5%.
- Animar solo `transform` y `opacity`; nunca `top/left/width` (provocan reflow).
- `content-visibility: auto` en secciones largas fuera de pantalla.

## Anti-patrones prohibidos
- Estilos inline en HTML (salvo variables dinámicas puntuales).
- Magic numbers sin comentario (`margin-top: 37px`).
- Sobrescribir en cascada lo que se acaba de definir — señal de arquitectura rota.
- `outline: none` sin reemplazo de indicador de foco.
