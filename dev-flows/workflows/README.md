# Dev-flows — dos carriles de ejecución (separados a propósito)

El sistema de flujos corre por **dos carriles independientes**. Están separados
deliberadamente para que, cuando **no haya memoria** para levantar agentes en paralelo,
el trabajo NO se pierda: el Carril A siempre puede terminar el flujo en solitario.

> **Regla de oro:** la lógica de *qué se hace en cada fase* vive en los `flow-*/SKILL.md`
> (única fuente de verdad). Los dos carriles solo cambian **CÓMO se ejecuta** esa lógica
> (un agente en serie vs. varios agentes en paralelo). Nunca dupliques las fases entre carriles.

---

## Carril A — Router secuencial (SIEMPRE disponible, sin coste de memoria)

- **Mecanismo:** `~/.kiro/steering/dev-flow-router.md` (`inclusion: always`) + los `flow-*/SKILL.md`.
- **Ejecución:** el agente activo corre las fases del flujo **en su propio turno, en serie**.
  Cero `spawn_run`, cero sub-agentes. No toca el guard de memoria.
- **Gate de entrada:** si la tarea trae clave Jira → `flow-po` primero → si APROBADO, encadena
  el `flow-*` de dev en el mismo turno.
- **Cuándo:** por defecto. Host con RAM ajustada (< 4 GB). CLI/CI headless. Cualquier momento
  en que el multi-agente no pueda arrancar.
- **Garantía:** funciona siempre. El orden depende de la disciplina del agente (reforzada por
  el Deliver gate embebido en cada skill).

## Carril B — Workflows multi-agente (requiere RAM ≥ `spawn_min_memory_gb`, hoy 4 GB)

- **Mecanismo:** scripts en `./workflows/*.py` (DSL `ctx`), ejecutados con el MCP tool
  `workflow_run(source=<contenido del .py>)`. El runtime del motor de workflows garantiza el orden.
- **Ejecución:** orquesta agentes `dev-*` como **nodos** (`ctx.agent(agent=...)`), en paralelo
  donde aplica (`ctx.parallel([...])`), con **gate + loop** de corrección garantizados por el runtime.
- **Cuándo:** host con RAM AMPLE (≥ 4 GB libres) y se quiere paralelismo real + garantía externa
  de secuencia (equivalente nativo al system.yaml+run.sh de MAFS).
- **Dependencia dura:** cada nodo se levanta vía spawn; con RAM por debajo del guard, el spawn
  se **rechaza** → el workflow no puede correr. Ese es el punto de fallback (ver abajo).

### Workflow único (`./workflows/master_dispatch.py`) — VALIDADO en runtime
UN solo workflow multi-agente. El PO analiza la HU de Jira, clasifica el tipo y ejecuta las
fases de ese tipo **inline** (con `ctx.agent`/`ctx.parallel`) en el mismo run. Una sola fuente
de verdad del grafo — sin `.py` por tipo duplicando la lógica.

| Tipo (lo dictamina el PO) | Grafo que ejecuta el maestro inline |
|---------------------------|-------------------------------------|
| `frontend` | implement → [standards ‖ security] gate/loop(3) → tests → deliver |
| `backend` | implement → [standards ‖ security] gate/loop(3) → compile+tests+contract → deliver |
| `fullstack` | **BACKEND** gate/loop → **FRONTEND** gate/loop → integración → deliver (multi-agente que se integra) |
| `data-migration` | implement → validate(rollback/EXPLAIN) → [standards ‖ security] gate/loop → deliver |
| `hotfix` | causa raíz+fix mínimo → build+tests → [standards ‖ security] gate/loop → verificación → deliver |
| `test` | escribir/reparar tests (solo test) → cobertura → deliver |
| `docs` | write (estándar) → sync check → deliver |

**Por qué un solo maestro y NO 7 `.py` por tipo:** `ctx.workflow` NO está cableado en este
host (verificado), así que un maestro no puede *orquestar* sub-workflows — tendría que
duplicarlos. Para evitar dos fuentes de verdad del mismo grafo, el maestro **contiene** las
fases de cada tipo (helpers `_run_<tipo>`) y NO hay `.py` sueltos por tipo.

**Auditorías en paralelo (lo que ahorra tiempo/coste):** en cada tipo que toca código, la
auditoría de estándares y la de seguridad corren **a la vez** (`ctx.parallel`), no una tras
otra, con loop de corrección de hasta 3 iteraciones antes de avanzar a tests/verificación.

**Fullstack multi-agente:** backend primero (su contrato debe existir), luego el frontend que
lo consume, y una fase de integración final — cada lado con su propio gate transversal.

**Validación** = `workflow_run(source=<master_dispatch.py>)` con args vacíos → debe terminar en
el guard `BLOCKED: faltan args` (status finished, error null). Es la verificación autoritativa.
Ejecución real: `workflow_run` con `{jira_key, repo, design_system}` y RAM ≥ 4 GB.

---

## Fallback (esto es lo que evita perder trabajo)

El **Carril B degrada al Carril A**, nunca al revés, y nunca falla en silencio:

1. Antes de un workflow, comprueba memoria (`resource_status`).
2. **RAM ≥ 4 GB** → corre el Carril B (`workflow_run`).
3. **RAM < 4 GB** → NO intentes el workflow (los spawns se rechazarían). Cae al **Carril A**:
   el agente ejecuta el mismo `flow-*` en serie en su turno, y lo **declara** en el Deliver gate
   ("multi-agente no disponible por memoria → ejecutado en sesión principal").
4. El resultado de cualquiera de los dos carriles es el mismo entregable (build/tests/auditoría
   con evidencia). Lo que cambia es el paralelismo, no el alcance.

Como los **`flow-*/SKILL.md` son la fuente de verdad de las fases**, el trabajo definido no
depende de que el workflow pueda correr: si B no arranca, A lo termina. Los scripts de `./workflows/`
son solo el *orquestador* de B — están a disco, versionados, y esperan a que haya memoria; no se
pierden ni bloquean el desarrollo mientras tanto.

## Fuente de verdad por artefacto
| Artefacto | Dónde | Carril |
|-----------|-------|--------|
| Fases de cada flujo | `~/.kiro/crew/skills/flow-*/SKILL.md` | A y B (compartido) |
| Router + gate de entrada | `~/.kiro/steering/dev-flow-router.md` (always) | A |
| Agentes dev-* | `~/.kiro/agents/dev-*.json` + prompts | A y B |
| Orquestador (grafo multi-agente) | `~/.kiro/crew/dev-flows/workflows/master_dispatch.py` (único) | B |
| Helpers/plantilla de gates | `~/.kiro/crew/dev-flows/workflows/_scaffold.py` (se COPIA inline) | B |

## Garantías estructurales de los workflows (`_scaffold.py`)

El motor **prohíbe `from ... import`** en los scripts de workflow (verificado:
"'from ... import' is not allowed in workflow scripts"). Por eso `_scaffold.py` **no es
importable**: es la **plantilla fuente** cuyos helpers se **copian inline** en cada script. Codifica,
como garantía de runtime, las reglas duras que un workflow de dev debe cumplir:

1. **`require_args(ctx, *names)`** → guard `BLOCKED: faltan args`. Permite **validar el script con
   `args` vacíos** antes del run real (debe terminar `finished` + `BLOCKED`, `error: null`). Atrapa
   los bugs del autor automático sin tocar el proyecto.
2. **`ctx.parallel([...])` SIEMPRE con lambdas** (nunca `ctx.agent(...)` evaluado → `TypeError:
   'str' object is not callable`).
3. **`audit_gate(...)`** → `dev-standards ‖ dev-security` en paralelo con loop de corrección
   obligatorio antes de verify.
4. **`contract_then_parallel(...)`** → fan-out contract-first: contrato → componentes independientes
   en paralelo → ensamble. Es el patrón para armar una pantalla cuyas piezas son independientes.
5. Tras borrar código, la auditoría verifica que **no quede dead code / huérfanos**.
6. **Respetar el alcance declarado**; no ampliarlo.

Así el grafo correcto es el camino fácil y los gates no dependen de que el agente los recuerde.
