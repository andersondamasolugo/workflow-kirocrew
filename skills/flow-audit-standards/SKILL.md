---
name: flow-audit-standards
description: Auditoría de estándares (clean code, arquitectura, convenciones) sobre el diff. Read-only, emite veredicto PASS/FAIL. Nativo KiroCrew. Lo ejecuta el agente dev-standards, típicamente como nodo transversal de un workflow.
always: false
triggers: audit standards, flow-audit-standards, auditar estandares, revisar estandares, standards gate
---

# flow-audit-standards — auditoría de estándares (gate read-only)

> ## 🎫 Flujo activo — AUDITORÍA DE ESTÁNDARES
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-audit-standards` |
> | **Tipo** | Auditoría transversal de estándares sobre el diff (read-only) |
> | **Agente** | `dev-standards` |
> | **Fases** | Identify diff → Auditar checklist → Veredicto |
> | **Orquestación** | 1 agente read-only; nodo de un workflow (paralelo a seguridad) |
> | **NO hace** | Escribir/corregir código, commit; auditar todo el repo (solo el diff) |
> | **Cierre** | Informe por severidad + `VERDICT: PASS\|FAIL` |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Gate de calidad read-only. Auditas el **diff** contra los estándares; no corriges nada.

## Fases

1. **Identify diff** — obtén el diff a auditar: `git diff` (working) o `git diff --staged`.
   Solo el diff, nunca todo el repo.
2. **Auditar checklist** — sobre el diff, aplica los estándares (se inyectan por su
   `inclusion`): nombres descriptivos, funciones pequeñas y de propósito único, tipado
   estricto (sin `any`/dict sin tipar), manejo de errores específico, sin dead code, imports
   ordenados, convenciones del stack (Angular/Java/Python/Node/SQL según los archivos tocados),
   estructura por dominio. Marca cada hallazgo con severidad + `archivo:línea`.
3. **Veredicto** — última línea exactamente `VERDICT: PASS` (sin ALTA/CRÍTICA) o
   `VERDICT: FAIL` (≥1 ALTA/CRÍTICA). Medium/Low se listan pero no cambian el veredicto.

## Orquestación de agentes
Flujo de UN agente read-only. **NO usa `spawn_run`**: es un nodo hoja invocado por un
workflow (en paralelo con `flow-audit-security`). No orquesta a nadie.

## Deliver gate — evidencia por fase (obligatorio, nativo)

Antes de declarar este flujo TERMINADO, vuelve a leer este mismo `SKILL.md` y, por CADA
fase que define arriba, emite una fila en esta tabla:

| Fase | Herramienta/comando ejecutado | Resultado (evidencia real) |
|------|-------------------------------|----------------------------|

Reglas del gate:
- Una fase SOLO cuenta como hecha si pegas la **evidencia real** de haberla ejecutado
  (salida del comando, no una afirmación). Sin evidencia = NO hecha.
- El veredicto debe respaldarse con el diff real auditado (pega el `git diff` o su resumen).
- Si no hay diff que auditar, decláralo **BLOCKED** con el motivo — nunca PASS "a ojo".
- No puedes emitir `VERDICT` sin haber leído el diff real.
- Este gate es la fase final y se aplica a sí mismo: es parte del flujo, no un extra opcional.
