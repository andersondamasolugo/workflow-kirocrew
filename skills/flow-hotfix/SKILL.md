---
name: flow-hotfix
description: Corrección urgente en producción, mínimo cambio, máxima verificación, nativo KiroCrew.
always: false
triggers: hotfix flow, flow-hotfix, hotfix, correccion urgente, fix produccion
---

# Flow Hotfix

> ## 🎫 Flujo activo — HOTFIX
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-hotfix` |
> | **Tipo** | Corrección urgente en producción (mínimo cambio) |
> | **Agente** | El del área afectada (front/back), según el incidente |
> | **Fases** | Causa raíz → Fix mínimo → Build+tests → Standards+Security → Verificación → Deliver |
> | **Orquestación** | Fases en esta sesión; `spawn_run` solo si hay paralelismo real |
> | **NO hace** | Refactors oportunistas, ampliar alcance más allá de la causa raíz |
> | **Cierre** | Deliver gate con evidencia (incidente resuelto, sin regresión) |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Corrección **urgente en producción**: el cambio más pequeño que resuelve el incidente,
con la mayor verificación posible antes de entregar. Orquestas las fases en esta sesión;
`spawn_run` solo si hay trabajo genuinamente paralelo. La seguridad del cambio pesa más
que la velocidad: un hotfix mal verificado es peor que el incidente.

## Fase 1 — Reproduce y aísla la causa raíz
- Reproduce el fallo de forma determinista antes de tocar código.
- Identifica la **causa raíz**, no el síntoma; confirma con evidencia (log, traza, test que falla).
- Declara en una línea qué está roto y por qué, antes del fix.

## Fase 2 — Fix mínimo
- El **cambio más pequeño** que resuelve la causa raíz. Sin refactors oportunistas ni
  limpieza colateral. Cada línea se justifica contra la causa de la Fase 1.
- Si el fix correcto es grande/arriesgado, propón un mitigante mínimo ahora y registra la
  deuda para un cambio posterior fuera del hotfix.

## Fase 3 — Build (config real) + tests afectados
- Compila con la config real (`tsconfig.app.json` en Angular), no solo specs.
- Ejecuta solo los **tests afectados** (host con memoria limitada). Build verde + tests OK
  antes de continuar.

## Fase 4 — Standards + Security sobre el diff
- Audita SOLO el diff (OWASP + estándares). **Critical/High bloquean** y se corrigen dentro
  del hotfix. Medium/Low se registran, no se corrigen aquí (no ampliar alcance).

## Fase 5 — Verificación
- **Frontend**: verificación visual nativa — `browser` MCP tool (panel del dashboard) →
  skill `web-verify` → playwright-cli fallback. Imagen-vs-imagen (antes/después); sin
  evidencia no hay PASS.
- **Backend**: valida contrato de la API afectada + tests del comportamiento corregido.
- Demuestra que el incidente está resuelto y sin regresión en el área tocada.

## Fase 6 — Deliver
- `git status`. **No commit.** Sugiere rama `hotfix/{HU}` y PR vía `prepare-pr`.
- Resume: causa raíz, cambio aplicado, verificación realizada.

## Reglas no negociables
1. Nunca commit/push sin autorización. 2. No ampliar el alcance del hotfix (solo la causa
raíz). 3. Build con config real. 4. Critical/High bloquean. 5. Sin evidencia de verificación
el hotfix no se declara resuelto.

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
