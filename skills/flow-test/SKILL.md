---
name: flow-test
description: Crear o reparar pruebas unitarias/E2E con cobertura, nativo KiroCrew.
always: false
triggers: test flow, flow-test, test only, escribir tests, reparar tests, cobertura
---

# Flow Test — Pruebas con cobertura

> ## 🎫 Flujo activo — TEST
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-test` |
> | **Tipo** | Crear/reparar pruebas unitarias/E2E con cobertura |
> | **Agente** | El del área bajo prueba (front/back) |
> | **Fases** | Identify → Write/Fix → Run con cobertura → (Paralelizar specs) → Deliver |
> | **Orquestación** | `spawn_run` para ≥2 specs rotos independientes; si no, en sesión |
> | **NO hace** | Modificar lógica de la app (un bug real se REPORTA, no se enmascara) |
> | **Cierre** | Deliver gate con cobertura ≥80% y bugs de producción reportados |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Trabajo centrado en **pruebas**: escribir tests para código sin cubrir o reparar specs
rotos, con cobertura medible. Regla que gobierna todo: **solo se tocan archivos de test,
nunca la lógica de la aplicación**. Si un test falla por un bug real de producción, se
**reporta** — no se cambia el código para forzar el verde.

## Fase 1 — Identify
- Qué código cubrir o qué specs están rotos y por qué.
- Runner real del stack (Angular → Jest; Python/FastAPI → pytest+httpx; Java/Spring →
  JUnit 5 + MockMvc). Nunca inventes framework.
- Lee el código bajo prueba y los tests existentes; replica el patrón del proyecto
  (fixtures, mocks, nombres).

## Fase 2 — Write / Fix
- Estructura **Given / When / Then**.
- **Mockea todas las dependencias externas** (red, DB, reloj, terceros). Ningún test consume
  backends reales.
- **PROHIBIDO modificar la lógica de la app** para pasar/cubrir. Solo archivos de test.
- Si un spec falla por un bug legítimo de producción: **detente y repórtalo** (archivo:línea
  + causa). No enmascares.
- Cubre casos límite y manejo de error, no solo el camino feliz.

## Fase 3 — Run con cobertura
- Suite afectada con cobertura (`jest --coverage`, `pytest --cov`, JaCoCo).
- Objetivo **≥80%** en lógica; **≥90%** en archivos tocados si el proyecto lo exige
  (revisa `sonar-project.properties`).
- Corre solo los afectados primero (host con memoria limitada); suite completa solo si hace
  falta. Todo verde antes de entregar.

## Fase 4 — Paralelizar specs rotos (condicional, spawn_run nativo)
- **≥2 specs rotos independientes** (distinto módulo/grupo, sin dependencia compartida):
  repártelos con `spawn_run` en UN batch, un task por spec (o grupo), pasando
  `cwd` = raíz del proyecto (permitida en `subagent_cwd_allowed_roots`, ej. `~/multi-agent-system/...`).
  Cada task: "repara `<archivo.spec>`; solo tocas ese archivo de test; corre su runner y pega el verde".
  Hasta el cap auto (piso 3, techo `subagent_auto_max`); el resto se encola solo. Espera TODOS
  los completion events antes de sintetizar.
- **1 solo**, o varios del **mismo grupo** (comparten fixture/mock/causa): corrígelos en esta
  sesión — sin fanout (un solo sub-agente no aporta paralelismo).
- Si un `spawn_run` se rechaza por memoria (`spawn_min_memory_gb`), corre los specs en la
  sesión principal en serie y decláralo en el Deliver gate.

## Fase 5 — Deliver
- `git status`. **Nunca commit ni push.**
- Reporta: cobertura obtenida, tests agregados/reparados, y cualquier bug de producción
  detectado que quedó **sin corregir** (por la regla de no tocar lógica).

## Reglas no negociables
1. Solo archivos de test. 2. Un fallo por bug real se reporta, no se enmascara. 3. Mockea
toda dependencia externa. 4. Usa el runner real del stack. 5. Entrega con `git status`, sin commit.

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
