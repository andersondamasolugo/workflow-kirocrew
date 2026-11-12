---
inclusion: always
---

# Changelog Standard — Seguros Bolívar

## Location and Format

Every repository must have a `CHANGELOG.md` at the root. Based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with organizational adaptations. Write entries in Spanish.

```markdown
# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionamiento Semántico](https://semver.org/lang/es/).

## [No publicado]

### Agregado
- Descripción del cambio nuevo

## [1.2.0] - 2026-04-15

### Agregado
- Nueva funcionalidad X que permite Y

### Cambiado
- Se modificó el comportamiento de Z para mejorar rendimiento

### Corregido
- Fix del bug que causaba error al hacer W
```

## Allowed Categories

Use exactly these categories (in Spanish), in this order. Omit empty categories.

| Category | When to use |
|---|---|
| **Agregado** | New features |
| **Cambiado** | Changes to existing features |
| **Obsoleto** | Features to be removed soon |
| **Eliminado** | Removed features |
| **Corregido** | Bug fixes |
| **Seguridad** | Vulnerability fixes |

## Writing Rules

Start each entry with `- `. Use past tense: "Se agregó", "Se corrigió", "Se eliminó". Reference Jira tickets when applicable: `(JIRA-1234)`. Be specific about what changed, where, and why if not obvious. The `[No publicado]` section accumulates changes until the next release.

Do NOT include minor refactors, code formatting, or trivial dependency updates. Group related changes into a single entry when it makes sense.

```markdown
# ✅ Good — specific, with Jira references
## [2.1.0] - 2026-04-15

### Agregado
- Se agregó módulo de evaluación de riesgo jurídico para iniciativas IA (JIRA-4521)

### Corregido
- Se corrigió error que impedía guardar formularios con más de 20 preguntas (JIRA-4498)

### Seguridad
- Se actualizó jsonwebtoken a v9.0.2 para corregir CVE-2024-XXXXX
```

```markdown
# ❌ Bad — vague, no references, no categories
## Cambios recientes

- fix bug
- se hicieron varios cambios
- merge de la rama feature/algo
```

## Versioning

Follow [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): Backward-compatible new features
- **PATCH** (0.0.X): Backward-compatible bug fixes

For projects without formal releases, use the date as version: `[2026-04-20]`. Dates always in `YYYY-MM-DD` (ISO 8601).

## When and Who

Update the changelog in the same PR as the change, not in a separate PR. The developer who makes the change is responsible for updating it. The PR reviewer must verify the changelog is updated. The tech lead validates the changelog before each release.

Commit message convention for changelog-only updates:

```bash
# ✅ Good
docs: actualizar changelog para v2.1.0

# ✅ Good — changelog updated as part of the feature commit
feat: agregar módulo de evaluación de riesgo jurídico (JIRA-4521)
```
