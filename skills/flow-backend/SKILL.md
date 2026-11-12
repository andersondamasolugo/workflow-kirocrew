---
name: flow-backend
description: Flujo end-to-end para desarrollo SOLO-BACKEND (servicios y APIs Spring/FastAPI/Express). Implementa sobre el stack aprobado, audita estándares+seguridad (OWASP) sobre el diff, compila, corre tests con cobertura y valida el contrato de la API. Nativo KiroCrew — la validación corre como fases embebidas de este skill. Úsalo cuando el cambio toca solo servicios/APIs, sin UI.
always: false
triggers: backend flow, run backend flow, flow-backend, service flow, api change flow
---

# flow-backend — flujo E2E solo-backend

> ## 🎫 Flujo activo — BACKEND
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-backend` |
> | **Tipo** | Backend-only (servicios/APIs Spring/FastAPI/Express) |
> | **Agente** | `dev-backend` (o `dev-integration` si es integración externa) |
> | **Fases** | Understand → Implement → Compile → Test → Contract check → Deliver |
> | **Orquestación** | 1 agente; `spawn_run` solo para ≥2 endpoints/specs independientes |
> | **NO hace** | UI, migraciones de esquema (usa `flow-data-migration`) |
> | **Cierre** | Deliver gate con evidencia real por fase |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Flujo nativo KiroCrew, ejecutado en esta sesión; la validación (compile + tests + contrato)
es una fase embebida de este skill, NO un hook del IDE (los `.kiro/hooks` no corren en el gateway).

## Fases

1. **Understand** — lee `projects/{proyecto}/.kiro/steering/*.md` + powers corporativos
   (error-handling, parameter-store, logging, swagger) + código existente. Replica el
   patrón existente, no inventes uno.
2. **Implement** — solo stack aprobado (Java/Spring, Python/FastAPI, Node/Express+Fastify).
   Type safety total (sin `any`/dict sin tipar). Validación de entrada siempre (Pydantic/Jakarta/Zod).
   Consultas parametrizadas (nunca SQL concatenado). Errores específicos, nunca catch desnudo.
   API First: rutas versionadas `/domain/api/v1/...`, OpenAPI, authz en el backend, PII enmascarada,
   logging estructurado con correlationId. Dependencias desde JFrog, versiones fijadas.
   (Audita cada archivo al escribirlo — fase embebida, no un hook del IDE.)
3. **Compile / typecheck** — el build real del stack (gradle/maven, mypy, tsc). Corrige hasta que quede limpio.
4. **Test** — tests unitarios (pytest+httpx / JUnit+MockMvc / Jest+Supertest), mockea deps
   externas, cobertura ≥80% en la lógica de negocio. Corrida dirigida en un host ajustado.
5. **Contract check** — el endpoint coincide con su OpenAPI/contrato (forma de request/response,
   códigos de estado, modelo de error). Validación y autorización presentes.
6. **Deliver** — `git status`, resumen. NO commit sin autorización. PR → `prepare-pr`.

## Orquestación de agentes (spawn_run nativo)
Las fases (implementar → compilar → test → contrato) son secuenciales dependientes, NO
fan-out. Delega vía `spawn_run` solo con trabajo genuinamente paralelo, `cwd` = raíz del
proyecto (permitida en `subagent_cwd_allowed_roots`):
- **≥2 endpoints/servicios independientes** (sin dependencia entre sí) → un batch, un task
  por endpoint, cada uno corre sus propias fases.
- **≥2 specs backend rotos independientes** → un batch, un task por spec.
- Análisis amplio de un log/dump grande → 1 sub-agente para aislar el contexto.
Integración externa (colas/eventos/terceros) → delega a `dev-integration` en vez de `dev-backend`.
Si un spawn se rechaza por memoria, corre en la sesión principal en serie.

## Notas
- Los sub-agentes SÍ pueden leer el FS del proyecto si `cwd` está bajo un root permitido
  (`subagent_cwd_allowed_roots`). Si un spawn se rechaza por memoria, corre la auditoría en la sesión principal.

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
