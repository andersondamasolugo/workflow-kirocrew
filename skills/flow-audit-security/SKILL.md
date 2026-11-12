---
name: flow-audit-security
description: Auditoría de seguridad (OWASP, secretos, inyección, authz, PII) sobre el diff. Read-only, emite veredicto PASS/FAIL. Nativo KiroCrew. Lo ejecuta el agente dev-security, típicamente como nodo transversal de un workflow.
always: false
triggers: audit security, flow-audit-security, auditar seguridad, revisar seguridad, security gate, owasp
---

# flow-audit-security — auditoría de seguridad (gate read-only)

> ## 🎫 Flujo activo — AUDITORÍA DE SEGURIDAD
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-audit-security` |
> | **Tipo** | Auditoría transversal de seguridad OWASP sobre el diff (read-only) |
> | **Agente** | `dev-security` |
> | **Fases** | Identify diff → Auditar OWASP → Veredicto |
> | **Orquestación** | 1 agente read-only; nodo de un workflow (paralelo a estándares) |
> | **NO hace** | Escribir/corregir código, commit; exponer secretos en claro |
> | **Cierre** | Informe por severidad + `VERDICT: PASS\|FAIL` |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Gate de seguridad read-only. Auditas el **diff** contra OWASP; no corriges nada.

## Fases

1. **Identify diff** — obtén el diff a auditar: `git diff` o `git diff --staged`. Solo el diff.
2. **Auditar OWASP** — sobre el diff: inyección SQL/NoSQL/comandos (consultas parametrizadas),
   secretos hardcodeados, validación de entrada, authz/IDOR (verificación de propiedad), XSS,
   SSRF, path traversal, fuga de PII/stack traces al cliente, dependencias con versión fija.
   Cada hallazgo: severidad + `archivo:línea` + riesgo en lenguaje de negocio + solución.
   Nunca pegues un secreto en claro: refiérete por nombre de clave.
3. **Veredicto** — última línea exactamente `VERDICT: PASS` (sin Critical/High) o
   `VERDICT: FAIL` (≥1 Critical/High). Medium/Low se listan pero no cambian el veredicto.

## Orquestación de agentes
Flujo de UN agente read-only. **NO usa `spawn_run`**: es un nodo hoja invocado por un
workflow (en paralelo con `flow-audit-standards`). No orquesta a nadie.

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
