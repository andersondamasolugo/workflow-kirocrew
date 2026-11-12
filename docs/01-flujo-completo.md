# Flujo completo de una HU

Pipeline estándar. Cada fase deja evidencia; sin evidencia no está hecha.

| # | Fase | Quién / qué skill | Salida |
|---|------|-------------------|--------|
| 0 | **Gate de requerimiento** | `flow-po` (agente `dev-po`) | Veredicto APROBADO o BLOQUEADO con criterios testables. Si bloquea, se detiene todo y decide un humano |
| 1 | **Entender / explorar** | Lectura del código real (`path:línea`) | Mapa corto de qué tocar. El mecanismo que dice la HU es una hipótesis: solo el síntoma es evidencia |
| 2 | **Especificar (SDD)** | `spec-workflow`, `spec-builder` | `requirements.md` (EARS), `design.md`, `tasks.md` |
| 3 | **Implementar (ODD)** | `flow-backend`, `flow-frontend`, `flow-fullstack`, `flow-data-migration` | Código + tests por unidad de comportamiento |
| 4 | **Calidad y seguridad pre-commit** | `flow-security-gate`, `sonar-local-gate` | `GATE: CLEAN` y `SONAR-LOCAL: CLEAN` |
| 5 | **Commit** | `work-unit-commits` | Un commit por unidad, Conventional Commits |
| 6 | **PR** | `templates/pr-footer.md`, `chained-pr` | PR sin conflictos, con las dos secciones obligatorias |
| 7 | **Revisión** | RDD / `judgment-day` / bot de code review | Hallazgos clasificados, no parchados uno a uno |
| 8 | **Promoción** | `docs/guia-pase-hu-a-master.md`, `skills/learnings/promote-*` | develop → stage → master sin arrastrar HUs ajenas |

## Qué flujo uso (router)

`steering/dev-flow-router.md` clasifica el pedido y carga el flujo:

| Tipo | Flujo |
|------|-------|
| Solo UI | `flow-frontend` |
| Solo servicio/API | `flow-backend` |
| UI + API | `flow-fullstack` (backend primero) |
| Esquema / migración | `flow-data-migration` |
| Urgencia en producción | `flow-hotfix` |
| Pruebas | `flow-test` (solo archivos de test) |
| Documentación | `flow-docs` |
| Trabajo multi-sesión | `flow-feature-doc` |

## Reglas no negociables

1. Nunca commit/push sin autorización explícita del desarrollador.
2. Verificar el build con la config real (`tsconfig.app.json` en Angular), no solo specs.
3. Standards y seguridad validados sobre el diff. Critical/High bloquean.
4. Design system al 100%: sin overrides ni hardcodes.
5. Atacar la **raíz**, no el síntoma. El fix correcto suele borrar, no agregar. Varios hallazgos con la misma causa = un solo fix.
6. Un commit = una unidad de comportamiento, con sus tests y docs. Nunca por tipo de archivo ni `git add .`.
7. Antes de crear un PR, mostrar el delta exacto (archivos + diff) y esperar el OK.
8. Verificar que el PR mergea limpio **antes** de crearlo (ver `docs/04-aprendizajes-pr.md`).
9. Comandos `git commit` y `git push` por separado, con rama explícita.

## Ejecución: dos carriles

- **Carril A (por defecto):** el agente activo corre las fases en serie. Siempre funciona.
- **Carril B:** workflows multi-agente en `dev-flows/workflows/` (`workflow_run`), solo cuando hay una razón nombrada (exploración grande, unidades independientes en paralelo, verificador independiente para cambios de alto riesgo).

Delegar a un subagente cuesta una sesión fresca y un handoff. El default es trabajar inline; delegar solo con una razón concreta.
