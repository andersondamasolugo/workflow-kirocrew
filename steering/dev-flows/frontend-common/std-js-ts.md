---
inclusion: fileMatch
fileMatchPattern: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "tsconfig*.json", "package.json"]
---

# Reglas JavaScript / TypeScript

## TypeScript primero
- Si el proyecto tiene `tsconfig.json`, TODO archivo nuevo es `.ts`/`.tsx`, nunca `.js`.
- `strict: true` obligatorio en `tsconfig.json` (incluye `noImplicitAny`, `strictNullChecks`).
- Prohibido `any`; usar `unknown` + narrowing. `as` solo con justificación en comentario.
- Tipar el dominio con `interface`/`type`; preferir uniones discriminadas sobre enums booleanos.
- Validar datos externos (API, formularios, env) con `zod` o similar — los tipos no existen en runtime.

## Estilo
- ESLint + Prettier configurados y en CI.
- `const` por defecto, `let` solo si se reasigna, `var` prohibido.
- Nombres: `camelCase` variables/funciones, `PascalCase` clases/componentes/tipos, `UPPER_SNAKE` constantes globales.
- Módulos ES (`import`/`export`); exportaciones nombradas sobre `export default` (mejor refactor y autocompletado).
- Comparación estricta `===` siempre.

## Asincronía
- `async/await` sobre cadenas `.then()`; nunca mezclar ambos estilos.
- Todo `await` dentro de `try/catch` o con manejo explícito en el borde.
- Nunca promesas flotantes: manejar o retornar cada promesa (`no-floating-promises`).
- `Promise.all` para operaciones independientes en paralelo.

## Errores
- Lanzar `Error` (o subclases propias), nunca strings.
- Errores de dominio tipados: `class PaymentDeclinedError extends Error`.
- En APIs: mapear errores a códigos HTTP correctos en una sola capa (middleware), no en cada handler.

## Patrones recomendados
- Funciones puras y módulos pequeños; la inmutabilidad por defecto (spread, `readonly`).
- Inyección de dependencias por parámetros/constructor; evitar importar singletons con estado.
- En React: componentes de función + hooks; estado derivado calculado, no duplicado; keys estables en listas.
- Separar lógica de negocio de la capa de UI/framework (servicios y hooks personalizados).

## Anti-patrones prohibidos
- Mutar props o estado directamente.
- Lógica de negocio en componentes de UI o en controladores HTTP.
- `setTimeout` para "esperar" condiciones (usar eventos/promesas).
- Dependencias sin fijar (`^`/`~` está bien con lockfile commiteado; lockfile obligatorio).

## Testing
- `vitest`/`jest` para unidad; Testing Library para componentes (probar comportamiento, no implementación).
- Tests e2e con Playwright para flujos críticos.
- No testear detalles internos: si un refactor sin cambio de comportamiento rompe el test, el test está mal.
