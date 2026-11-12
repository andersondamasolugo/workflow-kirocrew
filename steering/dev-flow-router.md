---
inclusion: always
name: dev-flow-router
description: Clasifica cada requerimiento de desarrollo por tipo y lo enruta al flujo (skill) y agente correctos. Mecanismo nativo de KiroCrew — sin orquestador externo, sin run.sh.
---

# Dev Flow Router

Antes de escribir código, clasifica el requerimiento en un tipo y carga el skill del
flujo que lo gobierna (`cat <skill-path>`). El flujo es parte de hacer el trabajo — no
necesitas que te lo recuerden.

## Gate de entrada obligatorio — PO PRIMERO (Jira → flow-po → dev)

Si la tarea **trae una clave Jira** (ej. `GD917-8478`) o pide **desarrollar una HU**,
SIEMPRE corre `flow-po` **PRIMERO**, en el mismo turno, antes de cualquier flujo de dev:

1. `flow-po` trae la HU (`@jira` → `jira_get_issue`), la evalúa y da veredicto.
2. **⛔ BLOQUEADO** → detente ahí (decisión humana). NO clasifiques ni desarrolles.
3. **✅ APROBADO** → clasifica el tipo con la tabla de abajo y **encadena el `flow-*` de dev
   correspondiente en el mismo turno** (no devuelvas el control al usuario para que lo pida).

`flow-po` NO es una fila alternativa de la tabla: es el **gate previo** de toda tarea con HU.

**Excepciones (NO disparan el gate):** trivial fix / typo / config de 1 línea; una pregunta o
conversación (no desarrollo); o una tarea de desarrollo **sin HU** que el usuario pide directo
(ahí clasifica con la tabla sin pasar por PO).

## Tabla de decisión

| Tipo | Señales | Flujo (skill) |
|------|---------|---------------|
| **Requirement gate (PO)** | Antes de desarrollar una HU: validar el requerimiento Jira | `flow-po` — **gate de entrada** (ver sección de arriba), trae la HU con `@jira` → `jira_get_issue`, valida criterios testables; BLOQUEA si es pobre, encadena al dev si APRUEBA |
| **Frontend only** | Solo UI: `*.component.ts/.html/.scss`, plantillas, estilos, navegación; sin cambio de API | `flow-frontend` — agente `dev-front-tienda` (PrimeNG/td-*) o `dev-front-bolivar-ui` (sb-ui-*) según design system |
| **Backend only** | Solo servicio/API: `*.py`/`*.java`/handlers, repos, mappers, lógica; sin UI | `flow-backend` — `dev-backend`, o `dev-integration` si es integración externa |
| **Fullstack** | UI + su servicio/endpoint | `flow-fullstack` — backend primero, luego el frontend que lo consume |
| **Database / migration** | Esquema, migración, índices, políticas de datos | `flow-data-migration` — agente `dev-database` |
| **Hotfix** | Corrección urgente en producción | `flow-hotfix` — mínimo cambio, máxima verificación |
| **Tests** | Crear/reparar pruebas, cobertura | `flow-test` — solo archivos de test |
| **Documentation** | README, changelog, OpenAPI, ADRs; sin cambio de comportamiento | `flow-docs` |
| **Pull request** | Abrir/preparar un PR | `prepare-pr` |
| **Sonar local (medir antes del commit)** | "corre sonar local", "sonar local al FE/BE", "sonar-gate", medir Sonar antes de subir | Skill `sonar-local-gate` — NO es SonarCloud: server Docker `localhost:9000`, token Keychain `sonar-local-token`, scanner en `~/tools` (no en el PATH del agente: el script lo encuentra solo). Comando: `python3 ~/.kiro/crew/dev-flows/scripts/sonar_local_gate.py <dir> --base origin/<base>`; FE = raíz del repo, BE = UN directorio `*-ms` por módulo tocado. Siempre pegar los links `dashboard:`/`issues:`; si da `BLOCKED`, arreglar ANTES del commit |
| **Security gate (pre-commit)** | ANTES de cada commit FE/BE: auditar OWASP el diff y reparar hallazgos | `flow-security-gate` — corre sobre el diff staged con las skills `secure-coding`/`-java`/`-frontend`, **DELEGA la reparación** de Critical/High al agente del stack (`dev-backend`/`dev-front-*`), re-audita y **BLOQUEA el commit** hasta `GATE: CLEAN`. Capa gemela del hook de calidad |
| **Meta — flujos/agentes** | Crear/cambiar/auditar un `flow-*` o un agente `dev-*` (mantener la maquinaria, no código de producto) | `agent-authoring` — agente `dev-flow-architect` |
| **Feature grande (multi-sesión)** | Trabajo que NO se retoma desde el diff: varias sesiones, esperas externas, o spec demasiado larga para sobrevivir compactación | `flow-feature-doc` — documento recuperable sobre `session_ledger_record`; NO reemplaza al `flow-*` de dev, lo sostiene entre cortes |
| **Trivial fix** | 1 línea, typo, config; sin decisión de diseño | Exento — fix directo + verificación mínima |

Si el requerimiento es ambiguo o mezcla tipos, pregunta antes de clasificar. Si es una
pregunta o conversación (no desarrollo), responde directo — no dispares un flujo.

## Cómo se garantizan los flujos (nativo de KiroCrew)

La automatización vive DENTRO del skill del flujo, no en hooks del IDE:

1. **El skill ordena la validación como fase obligatoria** — cada `flow-*` incluye
   implementar → auditar (standards+security sobre el diff) → build/tests → verificar →
   entregar. El agente las ejecuta en el mismo turno. Esto funciona en dashboard, chat y CLI.
2. **`config.json → hooks.auto_approve_tools`** permite que build/tests/lint corran sin
   aprobar cada comando (mínima intervención).
3. **`monitor_start` / `cron_add`** para vigilancia continua o programada (babysit de CI/PR).
4. **Router (este steering, `always`)** hace que clasifiques y cargues el flujo up front.

> Los hooks `.kiro/hooks/*.kiro.hook` (`fileEdited`/`agentStop`) son del **IDE de Kiro**,
> NO del gateway de KiroCrew. Sirven solo como refuerzo si el equipo además usa el IDE;
> la garantía en KiroCrew puro es la fase-en-skill de arriba, no un evento `agentStop`.

## Reglas no negociables (todos los flujos)

1. Nunca commit/push sin autorización explícita. Entrega = mostrar `git status`, detenerse.
2. Verificar el build con la config real (`tsconfig.app.json` en Angular), no solo specs.
3. Standards + security validados sobre el diff. Critical/High bloquean. El gate de seguridad
   accionable pre-commit es `flow-security-gate`: ANTES de cada commit FE/BE audita OWASP el diff
   staged, **DELEGA** la reparación de Critical/High al agente del stack y **bloquea el commit**
   hasta `GATE: CLEAN` (capa gemela del hook de calidad; ver su fila en la tabla).
4. Verificación visual de frontend = auto-verificación NATIVA: `browser` MCP tool (panel del
   dashboard, sin instalar nada) → skill `web-verify` → playwright-cli solo como fallback.
   Imagen-vs-imagen; sin evidencia no hay PASS (si no hay backend, BLOCKED, nunca PASS a ojo).
5. Design system al 100% — sin overrides, sin hardcodes.
6. Leer `projects/{proyecto}/.kiro/steering/*.md` + powers corporativos antes de escribir.
7. Los sub-agentes SÍ pueden leer el FS del proyecto vía `spawn_run` con `cwd` bajo un root
   permitido (`subagent_cwd_allowed_roots` incluye `~/multi-agent-system`). El fan-out real
   depende de DOS condiciones: (a) `cwd` bajo un root permitido, y (b) RAM del host por encima
   de `spawn_min_memory_gb` (hoy ~4 GB). Si el host está por debajo del umbral, el `spawn_run`
   es rechazado — corre esa parte en la sesión principal en serie y decláralo en el Deliver gate.
8. **Ataca la RAÍZ, no el síntoma — el fix correcto suele BORRAR, no agregar.** Antes de
   implementar cualquier corrección (en especial al remediar hallazgos de Sonar/OWASP o de un
   bot de review IA): si el fix agrega un estado, un flag, un verbo, una capa o una representación
   paralela de algo que ya existe → rediseña, casi siempre lo correcto es borrar o relajar algo.
   El MECANISMO que la HU/el reporte afirma es una hipótesis; solo el síntoma es evidencia:
   verifica contra el código real (`path:línea`) antes de tocar nada. Varios hallazgos con la
   misma causa = UN fix en la raíz, no N parches. Los hallazgos del bot de review IA son
   advisory y NO bloquean; no entres en el loop de implementar cada sugerencia (se sobre-diseña
   y el bot siempre encuentra más). Lo que bloquea es el gate real (Sonar Blocker/Critical,
   cobertura, ratings, Reliability A). → Aplica en Explore/Propón y en la remediación tras Sonar/OWASP.
9. **Commit por UNIDAD DE COMPORTAMIENTO, nunca por tipo de archivo ni `git add .`.** Un commit
   = un comportamiento/fix/migración entregable, con sus tests y docs en el MISMO commit. El repo
   debe seguir teniendo sentido aplicando solo ese commit, y el rollback de uno no debe borrar
   trabajo ajeno. Nada de "add models" / "add services" / "add tests" por separado. Aísla el delta
   con `git stash -u` + checkout selectivo cuando el working tree mezcla fix + workaround local +
   archivo ajeno; verifica con `git diff --cached --stat` que solo va lo esperado ANTES de
   commitear. Mensaje en Conventional Commits que explique el RESULTADO, no la lista de archivos.
   Si el cambio supera ~400 líneas, pártelo en unidades/PRs encadenados antes de implementar.
   → Aplica en Commit (fase Deliver, siempre con autorización de la regla 1).
10. **PR sin choques — verifica el merge ANTES de crearlo.** Una rama mergea limpio solo hacia la
    rama de la que fue CORTADA (o sus descendientes). El sufijo de la rama (`-to-master`/`-to-stage`),
    el BASE del PR y la rama de corte DEBEN coincidir — GitHub pone `develop` por defecto, cámbialo
    al ambiente correcto. Verifica ANTES de abrir el PR: `git fetch origin && git merge-tree --write-tree
    origin/<destino> origin/<rama>; echo $?` (0=limpio, 1=conflicto y lista los archivos imán). Antes
    de pushear un fix a una rama de PR, `gh pr view <n> --json state,mergedAt`: OPEN=misma rama;
    MERGED=rama fresca desde `origin/<base>` + cherry-pick (el push a una rama mergeada deja el commit
    huérfano). Nunca resuelvas conflictos en el editor web de un PR con target equivocado (arrastra el
    merge del ambiente y contamina la rama). `git push` como comando AISLADO, sin encadenar con `2>&1`
    o `&` (la policy bloquea el push si no puede verificar el destino). → Aplica en PR (fase Deliver).

> **Pipeline de una HU (encuadre de las reglas de arriba).** El recorrido típico de una HU
> —casi siempre ambigua— es: `flow-po` (gate, valida/BLOQUEA) → Understand/Explore (investiga
> contra el código real, criterio ODD para decidir si exploras con subagente — regla de delegación)
> → Propón (regla 8: a la raíz, sin sobre-diseño) → Implementa + unit tests (cobertura ≥80% propio)
> → Sonar/OWASP por LECTURA sobre el diff (reglas 3 y 8) → correr en local (build real, regla 2;
> visual si hay UI, regla 4) → **gate de seguridad pre-commit (`flow-security-gate`): audita OWASP
> el diff staged y DELEGA la reparación de Critical/High al agente del stack, bloquea hasta
> `GATE: CLEAN`** → Commit limpio (regla 9) → PR sin choques (regla 10). Cada fase
> entrega evidencia real en el Deliver gate del `flow-*`; sin evidencia no está hecha.

## Cuándo delegar — dimensiona por ENTENDIMIENTO, no por tamaño (criterio ODD)

Un subagente cuesta una sesión fresca, lecturas sin caché y un handoff. Por eso el default
es **trabajar inline en tu propio turno**: una tarea —aunque tenga varios pasos— casi siempre
se hace más rápido aquí que repartida. Dimensiona el trabajo por tres ejes, NO por cantidad
de archivos ni por líneas tocadas:

- **Entendimiento** — ¿ya sabes qué tocar, o necesitas explorar primero?
- **Riesgo** — ¿toca datos, seguridad, contratos compartidos, concurrencia, o un cambio que
  ningún test atraparía si rompe?
- **Resumibilidad** — ¿se puede retomar leyendo solo el diff, o el contexto se pierde entre
  sesiones (varias sesiones, esperas externas, spec demasiado larga para sobrevivir compactación)?

**Pequeño → inline (sin subagentes, sin documento).** Entendido, riesgo contenido y resumible
desde el diff. Es el caso por defecto; corre las fases del `flow-*` en serie en tu turno.

**Grande → un documento recuperable (session_ledger_record).** Solo cuando NO se puede retomar
desde el diff: varias sesiones, esperas externas, o requisitos tan largos que no sobreviven una
compactación. El ledger guarda el `next` concreto, lo intentado/rechazado y los punteros de
artefacto; cada retomar parte de ahí, no de tu memoria.

### Delega SOLO con una razón nombrada

Ninguna razón aplica por defecto; ante la duda, trabaja inline siguiendo el flujo. El conteo de
archivos, el tamaño de la tarea o un ratio de precio de modelo NUNCA deciden la ruta por sí solos:

| Razón | Cuándo aplica de verdad |
|-------|--------------------------|
| **Exploración** | Entender requiere más de un batch inline (≈3 calls y 10k tokens) o más de ~5 lookups secuenciales → un explorador read-only devuelve un mapa corto con evidencia `path:línea` |
| **Writers paralelos** | DOS o más unidades de comportamiento independientes (código+tests+docs juntos) con superficies de edición DISJUNTAS, cada una de varios minutos (≈100+ líneas): un subagente gasta 1–2 min leyendo antes de escribir. Una entrega que depende de otra NO es independiente |
| **Backstop de contexto** | Una sesión larga entrega su siguiente unidad acotada a un worker fresco |
| **Verificador independiente** | Un cambio de alto riesgo (datos, seguridad, contratos compartidos, concurrencia, entrega, o sin test que atrape la regresión) → un verificador que NO vio el contexto de esta sesión. Nunca el mismo modelo que escribió el cambio, ni "por si acaso" |

Nunca entregues el requerimiento entero a un solo worker para esperarlo y repetir su respuesta:
eso no es delegar, es agregar un salto. Si delegas, cada tarea declara su objetivo, insumos
listos, propiedad de archivos/worktree, salida verificable y condición de parada.

> Esto **refina** el Carril A/B de abajo: el Carril A (inline) es el default por ODD; el Carril B
> (workflow multi-agente) solo se justifica cuando se cumple una razón nombrada Y hay RAM. Antes
> estas reglas vivían implícitas en "sub-agentes solo para paralelismo real"; ahora son explícitas.

## Dos carriles de ejecución (Carril A por defecto; Carril B si hay memoria)

El MISMO flujo (`flow-*`) puede ejecutarse por dos carriles. Las fases son idénticas —
viven en el `SKILL.md` (única fuente de verdad); solo cambia CÓMO se ejecutan:

- **Carril A — router secuencial (SIEMPRE):** tú, el agente activo, corres las fases en tu
  turno, en serie. Sin `spawn_run`. No toca el guard de memoria. Es el default y el fallback.
- **Carril B — workflow multi-agente (RAM ≥ `spawn_min_memory_gb`):** un script en
  `~/.kiro/crew/dev-flows/workflows/*.py` ejecutado con `workflow_run` orquesta agentes `dev-*`
  como nodos, en paralelo, con gate + loop garantizados por el runtime.

**Regla de fallback (evita perder trabajo):** comprueba memoria con `resource_status`. Si
RAM ≥ 4 GB puedes usar el Carril B; si RAM < 4 GB NO intentes el workflow (los spawns se
rechazan) → ejecuta el Carril A y decláralo. El Carril B degrada al A, nunca al revés. Ver
`~/.kiro/crew/dev-flows/workflows/README.md`.

## Agentes parametrizados (steering nativo por inclusion)

Cada agente = su `prompt.md` (rol + qué design system usar) + el `skill://` de su flujo.
El **steering se resuelve de forma NATIVA por su `inclusion`**, NO forzado en `resources`:

- **Universal** (global `~/.kiro/steering/dev-flows/`): `_shared` (always), `frontend-common`,
  `backend`, `security`, `observability` — se aplican por su propio `inclusion`/`fileMatch`
  en toda sesión.
- **Design system** (POR PROYECTO, `<proyecto>/.kiro/steering/dev-flows-ds/`): `ds-tienda`
  (`td-*`/PrimeNG) o `ds-bolivar-ui` (`sb-ui-*`). Vive en el repo porque sus archivos
  `always` deben aplicar SOLO en ese proyecto — así no se mezclan los design systems.

| Agente | Variante / stack | Design system (por proyecto) |
|--------|------------------|------------------------------|
| `dev-po` | Gate de requerimiento Jira | — |
| `dev-front-tienda` | Front Tienda — PrimeNG / `td-*` | `ds-tienda` en el repo Tienda |
| `dev-front-bolivar-ui` | Front Bolívar UI — `sb-ui-*` | `ds-bolivar-ui` en el repo |
| `dev-backend` | Backend — Spring/FastAPI/Node | — |
| `dev-database` | Base de datos / migraciones | — |
| `dev-integration` | Integraciones externas | — |
| `dev-flow-architect` | **Meta** — crea/cambia/audita flujos y agentes (`agent-authoring`) | — |

Validación (standards, security), verificación visual y automatización E2E **no son agentes
seleccionables**: son **fases embebidas en los skills** y **capacidades** (web-verify,
browser). Sub-agentes vía `spawn_run` solo cuando se cumple una **razón nombrada** del criterio
ODD de arriba («Cuándo delegar»), nunca por tamaño de la tarea.

## Extender
Tipo nuevo = una fila aquí + un skill `flow-*`. Variante de agente nueva = un `.json` en
`~/.kiro/agents/` + su `prompt.md`. Design system nuevo = un módulo en `variants/` que el
`install.sh` copia al `.kiro/steering/` del proyecto.
