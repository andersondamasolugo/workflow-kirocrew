# SDD, ODD y RDD

Tres metodologías complementarias. Se usan según el tamaño y el riesgo del cambio.

## SDD — Spec-Driven Development (planear antes de codear)

Para HUs de peso o de alcance incierto. Se generan tres artefactos versionados en `.kiro/specs/<hu>/`:

| Artefacto | Responde | Contenido |
|-----------|----------|-----------|
| `requirements.md` | QUÉ | Requisitos en formato EARS (WHEN / IF / THE … SHALL), casos borde, supuestos explícitos |
| `design.md` | CÓMO | Arquitectura, contratos de API, errores, OWASP y Sonar integrados al diseño |
| `tasks.md` | PASOS | Checklist ordenado, cada tarea ligada a un requisito |

Principios:
- La calidad entra por diseño: Sonar (rating A, cobertura ≥ 80 %, duplicación ≤ 3 %, complejidad ≤ 15), OWASP (consultas parametrizadas, DTOs con allowlist, logs sin PII/tokens, secretos fuera del código).
- **Reutilizar antes de crear**: buscar un molde existente (servicio, modal, endpoint equivalente) y copiar su patrón.
- Un SDD no escribe código. Si el alcance es incierto, se hace con exploración de solo lectura y se compara cómo lo resuelven otras ARL/aseguradoras antes de proponer.
- Los requisitos de negocio que son inferencia del diseño **no se presentan como norma legal**. Se separa regla legal / regla de integridad de datos / inferencia.

Skills: `spec-workflow`, `spec-builder`.

## ODD — Organic Driven Development (cómo se ejecuta)

Protocolo que se aplica a cada pedido, proporcional al tamaño:

1. **Autorizar**: investigar/explicar/revisar es solo lectura; se cambia código solo con intención explícita.
2. **Explorar** lo mínimo necesario antes de proponer.
3. **Resolver incertidumbre**: una pregunta focalizada solo ante una decisión de producto real.
4. **Clasificar el tamaño**: *pequeño* = entendido, riesgo contenido y retomable solo con el diff → inline, sin documentos. *Grande* = no se retoma desde el diff (varias sesiones, esperas externas, spec larga) → `flow-feature-doc`.
5. **Implementar tarea por tarea**, tests primero (RED → GREEN → refactor) cuando hay un runner determinista.
6. **Cerrar** reportando resultado verificado, checks fallidos/pendientes y su línea de riesgo.

Riesgo alto (pide verificador independiente): datos irrecuperables o migraciones, seguridad, contratos que otros consumen, concurrencia, entrega/ambiente, o ningún test que atrape la regresión.

Delegación a subagentes solo con razón nombrada: exploración que excede un batch, unidades independientes con superficies de edición disjuntas, backstop de contexto, o verificación independiente de alto riesgo. Al lanzar un subagente de desarrollo, el brief **debe** decir explícitamente "crea y párate en la rama `feature/<HU>` antes de escribir".

Unidades de entrega: ~400 líneas autoradas por PR como heurística; sobre eso, PRs encadenados (`chained-pr`, `work-unit-commits`).

## RDD — Receipt-Driven Development (revisión con recibos)

Se corre antes del merge en repos donde el cambio lo amerita. Cada revisión deja un recibo con la identidad del candidato, su linaje y las correcciones. Reglas clave:

- Agrupar los defectos por invariante causal; un PR por invariante independiente.
- La validación del candidato la hace un lector independiente de solo lectura; un hallazgo implica un candidato nuevo.
- Los hallazgos del bot de code review son **advisory**. El gate real es Policy/Transversal checks + Sonar + cobertura. Ver `docs/04-aprendizajes-pr.md`.

Skill: `rdd-defect-workflow` (origen Gentle AI; respetar su licencia). Para una revisión adversarial a ciegas: `judgment-day` con los jueces de `agents/judgment-day/`.

## Cuándo usar cada una

| Situación | Camino |
|-----------|--------|
| Typo, config de una línea | Directo, verificación mínima |
| Cambio entendido y acotado | ODD inline |
| HU con alcance incierto o impacto transversal | SDD → ODD |
| Trabajo multi-sesión | ODD + `flow-feature-doc` |
| Cambio de alto riesgo | ODD + verificador independiente (+ RDD / Judgment Day) |
