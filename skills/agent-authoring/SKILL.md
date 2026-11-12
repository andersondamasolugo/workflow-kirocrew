---
name: agent-authoring
description: Estándar y auditoría para CREAR o REVISAR agentes de desarrollo (dev-*) con su flujo en KiroCrew. Define la estructura del JSON del agente, de su prompt.md y su acoplamiento nativo (skill del flujo + steering por inclusion + MCP globales sin credenciales embebidas + orquestación declarada). Úsalo al crear un agente nuevo, al revisar uno existente, o cuando el usuario pida auditar los agentes.
always: false
triggers: agent authoring, crear agente, nuevo agente dev, auditar agentes, revisar agentes, agent audit, estandar de agentes, dev agent
---

# agent-authoring — estándar y auditoría de agentes dev-* con flujo

Skill nativo KiroCrew. Gobierna cómo se crean y revisan los agentes de desarrollo
(`dev-po`, `dev-front-tienda`, `dev-front-bolivar-ui`, `dev-backend`, `dev-database`,
`dev-integration`, y futuros). NO es un flujo de código: es el contrato de construcción de
agentes + una auditoría verificable.

## Modo de uso
- **Crear**: sigue la plantilla (JSON + prompt), luego corre la Auditoría.
- **Revisar/Auditar**: corre la Auditoría sobre los agentes existentes y reporta hallazgos
  por severidad, como cualquier auditoría (no corrijas sin aprobación del usuario).

> Restricción del host: la política de seguridad bloquea comandos **shell** que referencien
> `~/.kiro/agents/`. Lee y edita los JSON con las herramientas `fs_read`/`fs_write`
> (`read`/`write`), NUNCA por `cat`/`grep`/`sed` de shell sobre esa ruta.

## 1. Anatomía del JSON del agente (`~/.kiro/agents/<agente>.json`)

Campos obligatorios y su regla:

| Campo | Regla |
|-------|-------|
| `name` | Igual al nombre de archivo, en kebab-case (`dev-front-tienda`). |
| `description` | Una línea: rol + qué flujo ejecuta + límite clave (design system / sin UI). |
| `model` | `"auto"` (hoy es el único disponible; no fijar otro sin acceso). |
| `prompt` | `file:///…/.kiro/crew/agents/<agente>/prompt.md` — el rol vive en el prompt, no inline. |
| `resources` | SOLO el skill de su flujo: `["skill://~/.kiro/crew/skills/flow-<x>/SKILL.md"]`. **NUNCA** listes steering aquí (rompe su `inclusion` nativo). |
| `mcpServers` | Solo `kirocrew-core`. **NO** declares un MCP con credenciales embebidas (Jira/Figma): se usan los **globales** de `~/.kiro/settings/mcp.json`. |
| `tools` | `fs_read`, `grep`, `glob`, `@kirocrew-core` + `fs_write`+`execute_bash` **si el rol escribe código** + `@<mcp-global>` que use por referencia (ej. `@jira`). |
| `allowedTools` | **IDÉNTICO a `tools`** (todo auto-aprobado) para que el flujo corra sin pedir permiso en cada build/test/escritura. Un `allowedTools` más corto que `tools` es un HALLAZGO. |

Reglas duras:
- **Secretos NUNCA embebidos** en el JSON del agente. MCP con credenciales → global; el
  agente lo referencia por nombre (`@jira`) y su prompt guía al usuario a configurarlo si falta.
- **Un solo flujo por agente** en `resources`. Si necesita dos, es dos agentes.
- Gate de lectura (ej. `dev-po`): **sin `fs_write`** — no escribe código.

## 2. Anatomía del prompt (`~/.kiro/crew/agents/<agente>/prompt.md`)

Orden de secciones (plantilla consistente):
1. **# <agente> — <rol> (Seguros Bolívar)**
2. **## Rol** — qué es y qué NO es.
3. **## Alcance** — lista `SÍ` / `NO` explícita.
4. **## Reglas del rol (NO NEGOCIABLE)** — design system / stack / seguridad según rol.
5. **## Flujo** — "Ejecutas `flow-<x>`" + las fases resumidas.
6. **## Precondición — MCP global** (si usa uno): qué hacer si el `@<mcp>` no está —
   DETENERSE y entregar al usuario la config conocida para pegar (el secreto lo pega él).
7. **## Steering aplicable (nativo por inclusion)** — recordar que se inyecta solo; leer
   primero el steering del PROYECTO activo.
8. **## Entrega** — `git status` + resumen; **nunca commit/push sin autorización**.

## 3. Acoplamiento nativo (verificado en kiro.dev)
- **Steering** se resuelve por su `inclusion` (always/fileMatch/manual) desde
  `~/.kiro/steering/**` (universal) o `<proyecto>/.kiro/steering/**` (design system por
  proyecto). NO se fuerza vía `resources` del agente.
- **Orquestación** (levantar sub-agentes) se **declara en el SKILL del flujo**, no en el
  JSON del agente: qué agentes, en qué orden, `cwd` bajo `subagent_cwd_allowed_roots`,
  esperar completion events, fallback si la memoria rechaza el spawn. Los flujos secuenciales
  declaran explícitamente que **NO** orquestan.
- **`.kiro/hooks`** (fileEdited/agentStop) son del IDE de Kiro, NO del gateway → la validación
  vive como **fase embebida del skill** (Deliver gate), no como hook.

## 3.1 Banner de flujo (🎫 Flujo activo) — obligatorio en cada `flow-*`
Todo `flow-*/SKILL.md` abre, justo bajo el `#` título, con un **banner uniforme** que hace
evidente qué flujo corre. Es la contraparte de entrada del Deliver gate (que es la de salida).
El agente **DEBE emitirlo al iniciar el flujo**. Formato canónico (7 campos):

```markdown
> ## 🎫 Flujo activo — <NOMBRE>
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-<x>` |
> | **Tipo** | <qué clase de trabajo> |
> | **Agente** | <agente(s) que lo ejecutan> |
> | **Fases** | <fase1 → fase2 → … → Deliver> |
> | **Orquestación** | <1 agente / spawn_run para X> |
> | **NO hace** | <límites explícitos> |
> | **Cierre** | <cómo se sabe que terminó> |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.
```

## 4. Auditoría (checklist verificable — corre esto al crear o revisar)

Por cada agente `dev-*`, verifica y reporta PASS/HALLAZGO:

**JSON**
- [ ] `name` == nombre de archivo, kebab-case.
- [ ] `model: "auto"` presente.
- [ ] `prompt` apunta a un `prompt.md` existente.
- [ ] `resources` = exactamente un `skill://flow-<x>` que existe en disco.
- [ ] `resources` NO contiene steering.
- [ ] `mcpServers` sin credenciales embebidas (sin token/apikey en claro).
- [ ] `tools` == `allowedTools` (misma lista).
- [ ] `@kirocrew-core` en ambos (habilita spawn_run/monitor_start).
- [ ] `fs_write`+`execute_bash` presentes si el rol escribe código; ausentes si es gate de lectura.
- [ ] MCP que usa por referencia (`@jira`, etc.) está en `tools` Y configurado global.

**Prompt**
- [ ] Secciones en el orden de la plantilla (Rol→Alcance→Reglas→Flujo→[Precondición MCP]→Steering→Entrega).
- [ ] Alcance con `SÍ`/`NO` explícito.
- [ ] "Ejecutas `flow-<x>`" coincide con el `resources` del JSON.
- [ ] Precondición de MCP global presente si usa uno (con config conocida para el usuario).
- [ ] Entrega dice "nunca commit/push sin autorización".
- [ ] Sin referencias muertas (scripts/archivos borrados, ej. helpers .py eliminados).

**Coherencia con el flujo**
- [ ] El `SKILL.md` del flujo referenciado existe y declara su orquestación (o su ausencia).
- [ ] El `dev-flow-router.md` lista el agente en su tabla.
- [ ] El `SKILL.md` del flujo tiene el **banner 🎫 Flujo activo** al inicio (bajo el `#` título),
      con los 7 campos: Flujo, Tipo, Agente, Fases, Orquestación, NO hace, Cierre — y la línea
      "Al iniciar el flujo, emite este banner". Un flujo sin banner es HALLAZGO MEDIA.
- [ ] El prompt del agente instruye emitir ese banner al arrancar el flujo (regla visible).

**Validación JSON**
- [ ] Cada JSON es sintácticamente válido (revísalo con `fs_read`; el shell está bloqueado en esa ruta).

## 5. Formato del informe de auditoría
Tabla ordenada por severidad, igual que una auditoría de seguridad:

| # | Severidad | Agente/Archivo | Hallazgo | Corrección propuesta |
|---|-----------|----------------|----------|----------------------|

Severidades: **ALTA** (rompe el flujo: allowedTools incoherente, secreto embebido, skill
inexistente), **MEDIA** (degrada: MCP no referenciado, precondición ausente), **BAJA**
(consistencia: front-matter, orden de secciones). NUNCA corrijas sin aprobación del usuario.

## 6. Anatomía de un FLUJO (`flow-*/SKILL.md`) — crear / auditar

Un flujo NO es solo un archivo suelto: es un contrato con 6 partes obligatorias. Al **crear**
un flujo nuevo, produce las 6; al **auditar**, verifica las 6.

1. **Front-matter** — `name` (== carpeta, `flow-<x>`), `description` (una línea: qué clase de
   trabajo + "Nativo KiroCrew"), `always: false` explícito, `triggers` (lista de frases que lo
   disparan). Idioma: **español** (consistencia con los flujos existentes).
2. **Banner 🎫 Flujo activo** — bajo el `#` título, los 7 campos de la sección 3.1.
3. **Fases numeradas** — cada flujo termina con **Deliver** (`git status` + resumen, nunca
   commit sin autorización). Frontend/hotfix incluyen **Build con config real** + **Visual**;
   backend incluye **Compile** + **Contract check**; todos los que tocan código incluyen
   **Standards+Security sobre el diff** (Critical/High bloquean). Cada fase es ejecutable con
   un comando real, no una afirmación.
4. **Orquestación declarada** — sección explícita: o bien "1 agente secuencial, NO usa
   `spawn_run`" (con el porqué), o bien las reglas de fan-out (`spawn_run` con `cwd` = raíz del
   proyecto bajo `subagent_cwd_allowed_roots`, solo trabajo genuinamente independiente,
   fallback a sesión principal si la RAM rechaza el spawn).
5. **Deliver gate — evidencia por fase** — el bloque estándar final (tabla fase→comando→
   evidencia real; sin evidencia = NO hecha; BLOCKED con motivo si no se puede ejecutar; nunca
   PASS "a ojo"). Es idéntico en los 8 flujos — cópialo tal cual.
6. **Registro en el router** — una fila en la tabla de decisión de `dev-flow-router.md`
   (`~/.kiro/steering/dev-flow-router.md`, `inclusion: always`) que enlaza señales → `flow-<x>`
   → agente. Un flujo sin fila en el router es un flujo huérfano (no se enruta).

### Checklist de auditoría de flujo (PASS/HALLAZGO por cada flow-*)
- [ ] Front-matter con `name`, `description`, `always: false`, `triggers`.
- [ ] Banner 🎫 con los 7 campos + línea "emite este banner al iniciar".
- [ ] Fases numeradas terminando en Deliver; sin commit/push sin autorización.
- [ ] Build/Compile con **config real** donde aplica; Standards+Security sobre el diff si toca código.
- [ ] Orquestación declarada explícitamente (orquesta con reglas de fan-out, o NO orquesta con el porqué).
- [ ] Bloque **Deliver gate — evidencia por fase** presente (idéntico al estándar).
- [ ] Fila en `dev-flow-router.md` que enruta a este flujo + su agente.
- [ ] Idioma español, sin secciones en inglés residual (`## Phases`/`## Notes`).
- [ ] Si el flujo introduce un agente nuevo, ese agente pasa la auditoría de la sección 4.

## 7. Flujo de trabajo del meta-agente (crear/cambiar/auditar)
- **Crear un flujo nuevo**: sección 6 (skill) + sección 1-2 (agente si hace falta uno nuevo) +
  registrar la fila en el router. Al terminar, corre la auditoría (4 + 6) sobre lo creado.
- **Cambiar un flujo**: edita el `flow-*/SKILL.md`; si cambian fases/orquestación, actualiza el
  banner, el router y el prompt del agente que lo ejecuta. Re-audita.
- **Auditar**: corre los checklists de la sección 4 (agentes) y 6 (flujos) y reporta con el
  formato de la sección 5. NUNCA corrijas sin aprobación del usuario.
- **Regla de oro nativa**: nada de hooks del IDE, nada de steering en `resources`, nada de
  secretos embebidos, el router es el único `always`. Verifica contra kiro.dev si dudas.
