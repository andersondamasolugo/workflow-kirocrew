---
name: flow-feature-doc
description: Crea y mantiene UN documento de feature recuperable para trabajo GRANDE (multi-sesión, con esperas externas, o spec demasiado larga para sobrevivir una compactación). Portado del "feature document" de ODD (Gentle-AI) sobre el ledger nativo de KiroCrew (session_ledger_record). NO es para trabajo pequeño: eso corre inline por su flow-* sin documento. Úsalo cuando el trabajo NO se puede retomar leyendo solo el diff.
always: false
triggers: feature doc, feature document, flujo grande, trabajo multi-sesion, documento recuperable, odd feature, flow-feature-doc, ledger de feature
---

# flow-feature-doc — documento de feature recuperable (ODD sobre ledger nativo)

> ## 🎫 Flujo activo — FEATURE DOC
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-feature-doc` |
> | **Tipo** | Meta-flujo de persistencia para trabajo GRANDE (no sustituye al `flow-*` de dev) |
> | **Backend** | `session_ledger_record` / `session_ledger_read` (nativo KiroCrew) |
> | **Fases** | Gate de tamaño → Crear doc → Ejecutar el flow-* real → Actualizar por hito → Cerrar |
> | **NO hace** | Correr para trabajo pequeño; reemplazar al `flow-frontend`/`flow-backend`/etc. |
> | **Cierre** | El ledger marca `done`/`abandoned` y para la inyección de snapshots |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Flujo nativo KiroCrew. Porta el **feature document** de ODD (Gentle-AI): para trabajo que NO
se puede retomar desde el diff, un único documento recuperable sostiene la spec verbatim, el
`next` concreto, lo intentado/rechazado y los punteros de artefacto. En KiroCrew ese documento
NO es un `.md` suelto — es el **ledger de sesión** (`session_ledger_record`), que ya sobrevive
compactación y se re-inyecta como `[work ledger]` en cada ciclo de monitor/wake.

## ⛔ Gate de tamaño — este flujo NO aplica a trabajo pequeño

Antes de crear nada, aplica el criterio ODD del router (`~/.kiro/steering/dev-flow-router.md`,
sección «Cuándo delegar»). Dimensiona por tres ejes, NO por cantidad de archivos:

- **Entendimiento** — ¿ya sabes qué tocar?
- **Riesgo** — ¿datos, seguridad, contratos compartidos, concurrencia?
- **Resumibilidad** — ¿se retoma leyendo solo el diff?

**Pequeño → NO uses este flujo.** Entendido, riesgo contenido y resumible desde el diff: corre
el `flow-*` de dev que corresponda **inline en tu turno**, sin documento ni ledger. Crear un
documento para trabajo pequeño es exactamente el sobre-proceso que ODD evita.

**Grande → SÍ, crea el documento.** Solo cuando el contexto se pierde entre sesiones:
- varias sesiones de trabajo,
- esperas externas (CI largo, aprobación de PR, despliegue, review de un tercero),
- requisitos tan largos que no sobreviven una compactación.

Si dudas, es pequeño: trabaja inline. El documento es la excepción, no el default.

## Fases

1. **Gate de tamaño** — decide con el criterio de arriba. Si es pequeño, DETENTE: no uses este
   flujo, ve al `flow-*` de dev inline. Declara en una línea por qué es grande (cuál de los tres
   ejes lo hace grande) antes de seguir.

2. **Crear el documento (abrir el ledger).** Una sola llamada `session_ledger_record` que fija:
   - `goal` — la spec/requerimiento **verbatim** (no parafraseado; ODD exige que el handoff
     apunte al texto exacto, no a un resumen). Si trae clave Jira, inclúyela.
   - `phase` — la fase de dev en que arranca (ej. `understand`, `implement`, `waiting_ci`).
   - `next` — el **intent concreto** del siguiente paso, no una palabra de estado. Mal: "seguir".
     Bien: "agregar el branch Windows a `_safe_chmod`, el test ya falla en `test_perms.py:88`".
   - `event` + `event_kind` — obligatorios al mover `phase` (ej. `event="feature doc abierto"`,
     `event_kind="milestone"`).
   - Punteros de artefacto cuando existan: worktree, branch, base_sha, PR.
   > Un solo documento por feature. No abras un ledger nuevo por cada sesión: se **actualiza**.

3. **Ejecutar el flow-* real.** El feature-doc NO reemplaza al flujo de dev: clasifica el tipo
   con la tabla del router y corre `flow-frontend`/`flow-backend`/`flow-fullstack`/etc. con sus
   fases y su Deliver gate. Este flujo solo SOSTIENE el contexto entre cortes.

4. **Actualizar por hito (no por cada edición).** Cada vez que cambie el estado real —una fase
   completada, un approach rechazado, una espera externa que empieza o termina— graba UN
   `session_ledger_record` con el `next` nuevo. Fields que omitas conservan su valor anterior
   (update parcial = lo normal). Registra sobre todo:
   - **lo intentado y rechazado** (y por qué) — evita repetir caminos muertos tras una
     compactación o un resume en sesión nueva;
   - el `next` actualizado como intent concreto;
   - punteros de artefacto nuevos (PR abierto, branch rebasada, base_sha nuevo).

5. **Resumir al retomar.** Al reanudar (sesión nueva, post-compactación, wake de monitor),
   `session_ledger_read` ANTES de re-derivar nada del chat. El `[work ledger]` snapshot y el
   `next` del ledger **mandan sobre tu recuerdo**. Sigue el `next`; no reconstruyas el plan de
   memoria.

6. **Cerrar.** Cuando el feature termina (o se abandona), graba `phase=done` (o `abandoned`) con
   su `event`. Eso **para la inyección de snapshots** del ledger. Entrega por el Deliver gate del
   `flow-*` que ejecutaste (evidencia real por fase); no declares "listo" con el ledger abierto.

## Relación con el resto de la maquinaria

- **Router** (`dev-flow-router.md`): su sección «Cuándo delegar» ya dice "Grande → un documento
  recuperable (`session_ledger_record`)". Este skill es el procedimiento concreto de ese caso.
- **Carril A/B**: ortogonal. El feature-doc sostiene contexto; el carril decide si las fases
  corren inline (A) o como workflow multi-agente (B). Un feature grande suele cruzar varios
  turnos en Carril A.
- **monitor_start / monitor_watch**: si la espera externa es un CI/PR, el feature-doc guarda el
  estado y el monitor vigila; al despertar, lee el ledger y sigue el `next`.
- **NO es un archivo .md en el repo.** El documento vive en el ledger nativo, no en disco del
  proyecto. Si el usuario quiere además un `.md` entregable (ADR, diseño), eso es `flow-docs`.

## Deliver gate — evidencia (obligatorio, nativo)

Antes de declarar este meta-flujo cumplido, emite esta tabla:

| Fase | Acción ejecutada | Evidencia real |
|------|------------------|----------------|

Reglas del gate:
- El **Gate de tamaño** cuenta como hecho solo si declaraste cuál eje hace grande al trabajo
  (o, si es pequeño, que NO se usó este flujo y se fue inline).
- "Crear/actualizar documento" cuenta solo si pegas el resultado real de `session_ledger_record`
  (no una afirmación de que lo grabaste).
- El trabajo de dev se entrega por el Deliver gate del `flow-*` que ejecutaste, con SU evidencia
  por fase — este flujo no la sustituye.
- No declares "feature listo" con el ledger aún abierto: ciérralo con `phase=done`/`abandoned`.
