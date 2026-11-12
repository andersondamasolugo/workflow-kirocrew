---
name: flow-docs
description: Flujo para trabajo de DOCUMENTACIÓN — README, CHANGELOG, specs OpenAPI/API, ADRs, doc comments — sin cambio de comportamiento en runtime. Sigue el estándar corporativo de changelog (español, categorías Keep a Changelog) y mantiene la doc en sync con el código. Nativo KiroCrew. Úsalo cuando la tarea es escribir o actualizar documentación.
always: false
triggers: docs flow, flow-docs, document this, update changelog, update readme, write docs
---

# flow-docs — flujo de documentación

> ## 🎫 Flujo activo — DOCS
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-docs` |
> | **Tipo** | Documentación (README, CHANGELOG, OpenAPI, ADR, doc comments) |
> | **Agente** | Cualquier dev del área; sin cambio de comportamiento runtime |
> | **Fases** | Locate → Write → Sync check → Deliver |
> | **Orquestación** | 1 agente secuencial — NO usa `spawn_run` |
> | **NO hace** | Cambiar comportamiento de código; build/test (no aplica) |
> | **Cierre** | Deliver gate; changelog estándar corporativo (español) |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Para trabajo que cambia documentación, no comportamiento en runtime. Nativo KiroCrew.

## Fases

1. **Locate** — encuentra el destino de la doc: `README.md`, `CHANGELOG.md` (o
   `.kiro/changelogs/changelog-<branch>.md`), spec OpenAPI, carpeta ADR, o el código
   cuyos doc comments hay que actualizar.
2. **Write** — sigue el estándar corporativo:
   - Changelog: español, categorías Keep a Changelog (Agregado/Cambiado/Obsoleto/
     Eliminado/Corregido/Seguridad), tiempo pasado, ref a Jira cuando aplique, sección
     `[No publicado]` preservada. Nunca borres/sobrescribas entradas existentes.
   - README por operación: Título, Descripción, API Path, Request/Response, Arquitectura,
     Built With, Endpoints, Autores.
   - OpenAPI: mantenlo como fuente de verdad; rutas versionadas.
3. **Sync check** — la doc coincide con el código actual (endpoints, params, ejemplos existen
   y son correctos). Sin referencias obsoletas.
4. **Deliver** — `git status`, resumen. NO commit sin autorización.

## Notas
- Solo-docs → sin gate de build/test: para cambios solo-docs no hay fase de build/tests.
- NO incluyas secretos/PII en los ejemplos — usa placeholders.

## Orquestación de agentes
Flujo de UN agente (escritura de documentación, secuencial). **NO usa `spawn_run`** — no hay
trabajo paralelizable.

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
