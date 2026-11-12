---
inclusion: fileMatch
fileMatchPattern: ["**/*.tsx", "**/*.jsx", "**/components/**", "next.config.*", "vite.config.*"]
---

# Reglas React (18+/19)

Aplican cuando el proyecto tiene `react` en `package.json`. Se suman a las reglas de
`javascript-typescript.md`.

## Componentes
- Solo componentes de función con hooks; nada de clases nuevas.
- Un componente por archivo, `PascalCase`, export nombrado.
- Componentes pequeños y presentacionales; la lógica vive en hooks personalizados (`useCart`, `useAuth`).
- Props tipadas con `interface`; desestructurar en la firma; máximo ~7 props (más = agrupar en objeto o repensar).
- Composición sobre configuración: `children` y slots antes que props booleanas infinitas.

## Estado
- Estado local mínimo: si se puede derivar de props u otro estado, se calcula, no se duplica.
- `useState` para estado simple; `useReducer` para transiciones complejas.
- Estado del servidor con TanStack Query/SWR (cache, reintentos, invalidación) — no `useEffect` + `fetch` manual.
- Estado global solo si de verdad es global (sesión, tema): Context para inyección de bajo cambio; Zustand/Redux Toolkit si hay actualizaciones frecuentes.
- Formularios con react-hook-form + validación zod; no controlar cada input con useState salvo casos simples.

## Efectos
- `useEffect` SOLO para sincronizar con sistemas externos (suscripciones, DOM, timers). No para transformar datos ni "reaccionar" a cambios de estado propios.
- Toda suscripción devuelve cleanup; dependencias completas (respetar `exhaustive-deps`).
- Evitar cascadas de efectos que se disparan entre sí — señal de estado mal modelado.

## Rendimiento
- Keys estables (id de datos), nunca el índice si la lista cambia.
- `memo`/`useMemo`/`useCallback` solo con problema medido, no por defecto.
- Code splitting por ruta con `lazy` + `Suspense`.
- Listas grandes: virtualización (react-window / virtua).

## Estructura y estilo
- Organización por feature (`features/cart/`) sobre organización por tipo (`components/`, `hooks/` globales gigantes).
- Manejo de errores con Error Boundaries por zona de la UI.
- Accesibilidad: elementos semánticos, `label` en inputs, foco gestionado en modales.

## Anti-patrones prohibidos
- `dangerouslySetInnerHTML` con datos de usuario sin sanitizar.
- Mutar estado (`items.push`) — siempre nuevas referencias.
- Definir componentes dentro de otros componentes (se remontan en cada render).
- Prop drilling de más de 2-3 niveles — extraer contexto o componer.

## Testing
- Testing Library: probar lo que el usuario ve y hace (`getByRole`), no la implementación.
- Mock de red con MSW, no mocks de fetch dispersos.
