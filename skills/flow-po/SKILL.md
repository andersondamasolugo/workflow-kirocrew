---
name: flow-po
description: Gate de calidad de requerimiento antes de desarrollar (con HU de Jira o con requerimiento en texto), nativo KiroCrew.
always: false
triggers: po flow, flow-po, validar requerimiento, revisar HU, quality gate, requerimiento jira
---

# flow-po — Gate de calidad de requerimiento (Product Owner)

> ## 🎫 Flujo activo — GATE DE REQUERIMIENTO (PO)
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-po` |
> | **Tipo** | Gate de requerimiento (con HU de Jira o requerimiento en texto) |
> | **Agente** | `dev-po` (solo lectura, sin `fs_write`) |
> | **Fases** | Determinar modo → Traer/leer requerimiento → Evaluar/derivar → Veredicto → (si APROBADO) Branch |
> | **Orquestación** | 1 agente secuencial — NO usa `spawn_run` |
> | **NO hace** | Escribir código, inventar criterios, auto-aprobar |
> | **Cierre** | Veredicto ✅ APROBADO / 📝 PROPUESTA / ⛔ BLOQUEADO + Deliver gate |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

El PO es el **primer contacto** de todo requerimiento. Valida la calidad **ANTES** de que
cualquier flujo de desarrollo escriba código. **No auto-aprueba** ni **inventa criterios que el
usuario no pidió**. Opera en **dos modos**:

- **Modo A — con HU (`jira_key`)**: trae la HU y la **evalúa críticamente**. Que exista NO es
  aprobación: la BLOQUEA si tiene vacíos, criterios no testables, criterios innecesarios o
  insuficientes, alcance ambiguo o contradicciones.
- **Modo B — sin HU (`requirement` en texto)**: no hay criterios formales → el PO los **deriva y
  propone**, y los **devuelve para confirmación humana** antes de aprobar.

## Fase 1 — Determinar el modo
- `jira_key` presente → **Modo A** (usa Jira).
- Solo `requirement` (texto) → **Modo B** (no usa Jira).
- Ninguno → **BLOQUEADO**: no hay nada que evaluar.

## Fase 2 — Traer / leer el requerimiento
- **Modo A**: el MCP de Jira está montado (tool `@jira`). Trae la HU con `jira_get_issue`
  (clave = código de la HU, ej. `GD917-8478`). Usa `jira_search` / `jira_get_issue_comments` si
  necesitas más contexto. Si el tool falla o la HU no existe, **detente** y repórtalo.
- **Modo B**: lee el requerimiento en texto tal cual lo dio el usuario. Jira NO se usa.

## Fase 3 — Evaluar (A) o derivar (B) — checklist única
Aplica la MISMA checklist en ambos modos:
- **Criterios de aceptación** presentes y **TESTABLES** (no "que funcione bien").
- **Alcance claro**: qué SÍ y qué NO entra.
- **Entradas/salidas** con ejemplos (formatos, payloads, valores).
- **Casos límite** y **manejo de error** esperado.
- **Dependencias** (servicios, APIs, otras HU, datos).
- **Restricciones**: rendimiento, compatibilidad, versiones, ambiente.

Detecta fallas lógicas: **contradicciones** (pide A y B pero A excluye B), **supuestos falsos**
(endpoint/componente que no existe), **problema XY** (pide la solución intentada, no el objetivo).

- **Modo A**: marca cada punto presente/ausente sobre la HU. Señala además criterios
  **innecesarios/redundantes** para recortarlos. Vacío o criterio no testable = motivo de BLOQUEO.
- **Modo B**: **deriva** los criterios de aceptación testables a partir del texto (no los
  inventes más allá de lo pedido; extrae lo implícito y decláralo). Si el texto es insuficiente
  para derivar criterios testables, es BLOQUEADO.

## Fase 4 — Veredicto
**📝 PROPUESTA** (solo Modo B, paso previo) — devuelve los criterios derivados y **detente**:
```
PROPUESTA — criterios de aceptación derivados del requerimiento:
Objetivo: [una línea]
Alcance: [qué se toca y qué NO]
Criterios de aceptación (testables):
- [criterio 1]
- [criterio 2]
Supuestos: [declarados]
Confirma o ajusta para continuar al desarrollo.
```
No encadenas a dev hasta que el humano confirme.

**✅ APROBADO** — Modo A que cumple la checklist, o Modo B ya confirmado por el humano. Resume:
```
Objetivo: [una línea]
Alcance: [qué se toca y qué NO]
Criterios de aceptación: [lista testable]
Supuestos: [declarados si hay]
```
**Encadena en el MISMO turno**: clasifica el tipo con `dev-flow-router.md` y carga el
`flow-*` de dev correspondiente (`cat <skill>`) — NO devuelvas el control al usuario para que
lo pida. El gate y el flujo de dev corren seguidos.

**⛔ BLOQUEADO** — pobre/ambiguo/insuficiente (venga de Jira o texto). **Detente** (decisión
humana). Lista exactamente qué falta en un solo mensaje:
```
BLOQUEADO — el requerimiento no está listo para desarrollo.
Falta:
- [ítem concreto 1]
- [ítem concreto 2]
Modo A: corrige la HU en Jira y vuelve a ejecutar flow-po.
Modo B: reescribe el requerimiento con lo faltante y vuelve a ejecutar flow-po.
```
No avances a desarrollo mientras esté BLOQUEADO.

## Fase 5 — (solo si APROBADO) Recomendar branch
`feature/{HU}-descripcion-corta` (ej. `feature/CIENHE-1022-shopping-cart`). En Modo B sin HU,
usa una descripción corta derivada del objetivo.

## Reglas
- Nunca inventar criterios que el usuario no pidió (Modo A: si no están, faltan. Modo B: deriva
  lo implícito del texto y decláralo como propuesta, no como hecho).
- Un requerimiento ambiguo se devuelve (BLOQUEADO), no se rellena.
- El PO valida; no auto-aprueba. En Modo B, los criterios derivados requieren confirmación humana.
- El paso a desarrollo ocurre solo tras APROBADO.

## Orquestación de agentes
Flujo de UN agente (gate de lectura/validación, secuencial). **NO usa `spawn_run`** — no hay
trabajo paralelizable; delegar aquí solo añadiría round-trips.

## Deliver gate — evidencia por fase (obligatorio, nativo)

Antes de declarar este flujo TERMINADO, vuelve a leer este mismo `SKILL.md` y, por CADA
fase que define arriba, emite una fila en esta tabla:

| Fase | Herramienta/comando ejecutado | Resultado (evidencia real) |
|------|-------------------------------|----------------------------|

Reglas del gate:
- Una fase SOLO cuenta como hecha si pegas la **evidencia real** de haberla ejecutado
  (salida del comando, no una afirmación). Sin evidencia = NO hecha.
- Prohibido sustituir un paso por un atajo más barato (p. ej. type-check de specs o
  `sass.compile` en lugar del build real que la fase de Build exige). El atajo NO es evidencia.
- Si una fase no se puede ejecutar en este host/entorno, decláracla **BLOCKED** con el motivo
  concreto y qué falta para desbloquearla — nunca la marques PASS "a ojo".
- No puedes decir "listo"/"flujo cumplido" con filas sin evidencia ni BLOCKED justificado.
- Este gate es la fase final y se aplica a sí mismo: es parte del flujo, no un extra opcional.
