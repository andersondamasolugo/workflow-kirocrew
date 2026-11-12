---
name: flow-data-migration
description: Flujo nativo KiroCrew para migración de datos y esquemas de base de datos (versionada, compatible hacia atrás, con rollback verificado).
always: false
triggers: data migration flow, flow-data-migration, migracion de datos, migracion de esquema, db migration
---

# Flow — Data Migration

> ## 🎫 Flujo activo — DATA MIGRATION
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-data-migration` |
> | **Tipo** | Migración de datos/esquema de base de datos |
> | **Agente** | `dev-database` |
> | **Fases** | Understand → Design → Implement → Validate → Standards+Security → Deliver |
> | **Orquestación** | 1 agente secuencial — NO usa `spawn_run` (integridad de datos) |
> | **NO hace** | UI, lógica de servicio ajena a la migración, `DROP` sin rollback |
> | **Cierre** | Deliver gate con evidencia real (rollback verificado) |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Flujo end-to-end para cambios de datos y de esquema de base de datos: migración
versionada, compatible hacia atrás y con rollback verificado. Tú **orquestas todo
dentro de esta sesión** — no dependes de hooks del IDE; las fases se ejecutan en
orden aquí mismo, y la auditoría de estándares y seguridad va embebida sobre el
diff antes de entregar.

## Fase 1 — Understand
- Lee el steering del proyecto (`projects/{proyecto}/.kiro/steering/*.md`) y el power
  correspondiente antes de escribir nada.
- Revisa el esquema actual: tablas, columnas, tipos, PK, FK, índices y restricciones que
  toca la migración.
- Identifica el motor y la herramienta de migraciones ya en uso (Flyway/Liquibase para
  Java-Spring, Alembic para Python-FastAPI, node-pg-migrate para Node). No introduzcas una
  herramienta nueva si el proyecto ya tiene una.
- Determina qué código de aplicación lee/escribe las columnas afectadas.

## Fase 2 — Design migration
- Migración **versionada** con la herramienta del stack.
- **Compatible hacia atrás** (expand/contract): 1) agregar columna nueva (nullable/default);
  2) desplegar el código que la usa; 3) backfill si aplica; 4) eliminar la vieja en una
  migración **posterior**, ya sin lectores.
- **Nunca** un `DROP` destructivo sin respaldo verificado y plan de rollback escrito.
- Documenta el plan: qué hace cada migración, orden de despliegue, cómo se revierte.

## Fase 3 — Implement
- Script **idempotente** (`IF NOT EXISTS`/`IF EXISTS`).
- Tipos correctos: dinero `NUMERIC(19,4)` (nunca `FLOAT`), `BOOLEAN`, `TIMESTAMPTZ`.
- `NOT NULL` por defecto (default o backfill previo al agregarlo a tabla con datos).
- FKs con `ON DELETE` **explícito y consciente**.
- Escribe la migración `up` y su `down`/rollback.

## Fase 4 — Validate
- Corre la migración en **entorno de prueba** (nunca directo en compartido).
- Verifica el **rollback** (`down` restaura el estado previo).
- `EXPLAIN` sobre las consultas afectadas (siguen sargables y usando índices).
- Confirma que el código sigue compilando/pasando tests con el esquema nuevo.

## Fase 5 — Standards + Security (embebido)
Audita el **diff**: SQL en MAYÚSCULAS, identificadores `snake_case`, tablas en plural,
`created_at`/`updated_at`, sin `SELECT *`; sin secretos, consultas parametrizadas, mínimo
privilegio, sin PII en claro. Critical/High se corrigen antes de seguir.

## Fase 6 — Deliver
- Muestra `git status`. **NO commit sin autorización.**
- Resume: qué migra, orden de despliegue, cómo se revierte, qué queda pendiente.

## Reglas
- Nunca commit sin autorización. **Migraciones inmutables** una vez aplicadas en ambientes
  compartidos: los cambios van en una migración NUEVA, nunca editando una aplicada.
- Nunca `DROP` destructivo sin respaldo y rollback. Compatible hacia atrás durante despliegues.
- No introducir motor/herramienta fuera del stack aprobado del proyecto.

## Orquestación de agentes
Flujo de UN agente. **NO usa `spawn_run`**: una migración con rollback verificado es
secuencial y sensible — paralelizarla arriesgaría la integridad de los datos.

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
