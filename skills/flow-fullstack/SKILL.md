---
name: flow-fullstack
description: Flujo end-to-end para desarrollo FULLSTACK (un cambio de UI Y su servicio/endpoint de respaldo). Contract-first: define el contrato de la API primero, luego backend y frontend se construyen contra él (en paralelo en el Carril B, en serie en el Carril A), más un chequeo de integración de que la UI y el servicio concuerdan en el contrato. Nativo KiroCrew. Úsalo cuando tanto un cambio de UI como su API/servicio están en alcance.
always: false
triggers: fullstack flow, run fullstack flow, flow-fullstack, front and back, end to end feature
---

# flow-fullstack — flujo E2E fullstack

> ## 🎫 Flujo activo — FULLSTACK
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-fullstack` |
> | **Tipo** | Fullstack (un cambio de UI + su servicio/endpoint) |
> | **Agente** | `dev-backend`/`dev-integration` → luego `dev-front-tienda`/`dev-front-bolivar-ui` |
> | **Fases** | Contrato → (Backend ‖ Frontend) → Integración → Deliver |
> | **Orquestación** | **Contract-first:** contrato SERIAL primero; luego Backend ‖ Frontend EN PARALELO contra el contrato (Carril B). Carril A los corre en ese mismo orden pero en serie (una sesión) |
> | **NO hace** | Migraciones de esquema (usa `flow-data-migration`) |
> | **Cierre** | Deliver gate con evidencia real por fase (ambos lados) |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

**Contract-first, no backend-first.** Lo que debe existir antes que ambos lados es el CONTRATO,
no el backend completo. Con el contrato fijo, el frontend ya no depende de que el backend esté
implementado: ambos construyen contra el contrato. Por eso, una vez definido el contrato, backend y
frontend corren EN PARALELO en el Carril B (workflow/spawn); en el Carril A (una sola sesión, sin
spawn) se corren en serie en el mismo orden. Nativo KiroCrew — la validación de cada lado es una fase
embebida del flujo, NO un hook del IDE (los `.kiro/hooks` no corren en el gateway).

## Fases

1. **Plan del contrato (SERIAL, primero)** — define el contrato de la API (ruta, request/response,
   estado, modelo de error) como artefacto compartido. Es la única fuente de verdad; ambos lados
   construyen contra él. Prerequisito de todo lo demás.
2. **Backend ‖ Frontend (contra el contrato)** — con el contrato fijo, ambos lados se implementan:
   - **Carril B (workflow/spawn):** EN PARALELO — backend (`flow-backend`) y frontend (`flow-frontend`)
     a la vez, cada uno cableado al contrato de la fase 1.
   - **Carril A (una sesión, sin spawn):** en SERIE, en el mismo orden (backend, luego frontend).
   No es necesario dejar el backend implementado antes de tocar la UI: basta con el contrato.
3. **Gate transversal** — estándares ‖ seguridad sobre el diff combinado (con loop de corrección) +
   build/tests de cada lado tocado (verificación visual imagen-vs-imagen si el front cambió).
4. **Integration check** — verifica que UI ↔ servicio concuerdan EXACTAMENTE con el contrato de la
   fase 1: forma del request, mapeo de la respuesta, manejo de error, estados loading/empty. Si un
   mock reemplazó al servicio, confirma que el contrato real coincide.
5. **Deliver** — `git status`, resumen combinado (backend + frontend). NO commit sin
   autorización. PR → `prepare-pr`.

## Orquestación de agentes (spawn_run nativo) — contract-first paralelo
Este flujo delega cada lado a su agente especialista vía `spawn_run`, pasando
`cwd` = raíz del proyecto (permitida en `subagent_cwd_allowed_roots`):

1. **Contrato primero (SERIAL, prerequisito compartido)** — define el contrato como artefacto:
   `spawn_run(agent="dev-backend", task="<solo el contrato de la API: rutas, request/response, estados, errores>", cwd="<repo>")`.
   Espera su completion event. Su salida es la fuente de verdad para ambos lados.
2. **Backend ‖ Frontend EN PARALELO (contra el contrato)** — en UN solo `spawn_run` batch, porque
   con el contrato fijo ya NO son dependientes:
   `spawn_run(tasks=["<backend: implementa el endpoint contra el contrato>", "<frontend: UI que consume el contrato>"],
   agents=["dev-backend" (o "dev-integration"), "dev-front-tienda" (o "dev-front-bolivar-ui" según design system)], cwd="<repo>")`.
   Espera AMBOS completion events antes de seguir.
3. **Gate + integración después, una sola vez** — sobre el diff combinado: estándares ‖ seguridad,
   build/tests de cada lado, y el integration check contra el contrato. (Solo IMPLEMENT va en el
   batch paralelo; el gate NO se anida dentro del paralelo.)
4. **Fan-out adicional dentro de un lado** — p. ej. varios endpoints independientes pueden ir como
   tareas extra del mismo batch (hasta el cap auto).

Si un `spawn_run` es rechazado por memoria (`spawn_min_memory_gb`) o corres el **Carril A** (sin
spawn), ejecuta contrato → backend → frontend → gate → integración EN SERIE en la sesión principal,
en ese mismo orden contract-first, y decláralo en el Deliver gate. El Carril B degrada al A, nunca al revés.

## Notas
- Los sub-agentes SÍ pueden leer el FS del proyecto si `cwd` está bajo un root permitido
  (`subagent_cwd_allowed_roots` incluye `~/multi-agent-system`). Si un spawn se rechaza por
  memoria, corre ese lado en la sesión principal.
- La validación (build + tests) de cada lado tocado es una fase obligatoria del flujo, no
  un hook del IDE — corre en el mismo turno.

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
