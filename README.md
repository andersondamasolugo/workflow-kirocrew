# workflow-kirocrew · Kiro GB Workflow

Configuración compartida de **buenas prácticas de desarrollo en Gestión Bienestar (GB)** para Kiro Crew: agentes, skills, reglas (steering), scripts y guías. Sirve para que todo el equipo desarrolle con los mismos criterios, sin armar el flujo a mano en cada máquina.

> Este repo **no contiene secretos**. Los tokens, correos y credenciales los configura cada persona en su máquina.

## Cómo se usa (30 segundos)

1. Abrí un chat nuevo en **Kiro Crew**.
2. Pegá este mensaje:

   > Instalá y configurá el workflow de este repo: https://github.com/andersondamasolugo/workflow-kirocrew.git (seguí las instrucciones de `AGENTS.md`).

3. Kiro clona el repo, valida que no haya secretos, instala los agentes, skills y reglas en `~/.kiro`, y te guía con lo único que tenés que poner vos (tokens de Jira y Sonar, JFrog, identidad de git).
4. **Abrí una sesión nueva**. Los agentes, skills y reglas se cargan al iniciar la sesión; las ya abiertas no los ven.

Listo: desde ese momento, cuando pidas una HU por su clave Jira (por ejemplo `GD929-1234`), Kiro sigue el flujo del equipo.

**Windows:** Kiro detecta el sistema y usa `install.ps1`. Guía y diferencias en [docs/06-windows.md](docs/06-windows.md).

Instalación manual (macOS/Linux), si preferís:

```bash
git clone https://github.com/andersondamasolugo/workflow-kirocrew.git
cd workflow-kirocrew
./install.sh --dry-run   # ver qué copiaría
./install.sh             # instalar; no pisa archivos existentes
./install.sh --force     # pisar, con backup en ~/.kiro/.gb-backup-<fecha>
```

Si algo falla al instalar, Kiro prepara un reporte con los datos sensibles redactados, te lo muestra y, con tu OK, abre un issue en este repo (etiqueta `install-failure`) para repararlo después.

## Qué te cambia en el día a día

Al pedir una HU, el router (`steering/dev-flow-router.md`) lo ordena todo:

```
HU en Jira
  └─ flow-po         valida la HU; si es pobre, BLOQUEA y decide una persona
       └─ SDD        requirements → design → tasks (si el alcance lo amerita)
            └─ ODD   implementar por unidad de comportamiento, tests primero
                 └─ Gates pre-commit: tests + cobertura ≥ 80 % + Sonar local + OWASP
                      └─ Commit por unidad → PR sin choques con plantilla obligatoria
                           └─ Revisión (RDD) → promoción develop → stage → master
```

Reglas que aplica siempre:

- Nunca hace commit ni push sin tu autorización explícita.
- Antes de crear un PR te muestra el delta exacto y espera tu OK.
- Un commit = una unidad de comportamiento, con sus tests y docs.
- Ataca la causa raíz; varios hallazgos con la misma causa se arreglan con un solo cambio.
- Todo PR termina con *Relación de Historias de Usuarios* y *Tipos de Cambios* (`templates/pr-footer.md`).

## Qué contiene

| Carpeta | Contenido |
|---------|-----------|
| `AGENTS.md` | Instrucciones para que el agente se autoinstale |
| `agents/` | Agentes `dev-*` (backend, frontend Tienda y Bolívar UI, DB, integración, PO, seguridad, estándares, arquitecto de flujos) y jueces de Judgment Day |
| `skills/` | Flujos `flow-*`, gates de seguridad, `secure-coding-*`, Sonar local, SDD, commits por unidad, PRs encadenados |
| `skills/learnings/` | Aprendizajes reales de HUs y PRs convertidos en procedimientos (promoción entre ramas, Sonar, Jira, Oracle MCP, E2E) |
| `steering/` | Reglas permanentes: stack aprobado, seguridad, estilo, arquitectura, changelog, observabilidad, Angular y Java |
| `dev-flows/` | Scripts de Sonar local, workflows multi-agente y plantillas |
| `templates/` | Plantilla del pie de PR |
| `docs/` | Guías detalladas |
| `install.sh` / `install.ps1` | Instaladores a `~/.kiro` (macOS/Linux y Windows) |
| `scripts/report_install_issue.py` | Genera (y con tu OK crea) el issue de una instalación fallida, con datos redactados |
| `scripts/check-secrets.sh` | Chequeo de secretos y datos personales antes de cada commit |

## Documentación

1. [Flujo completo de una HU](docs/01-flujo-completo.md)
2. [SDD, ODD y RDD](docs/02-sdd-odd-rdd.md)
3. [Sonar local](docs/03-sonar-local.md)
4. [Aprendizajes de PR](docs/04-aprendizajes-pr.md)
5. [Onboarding y configuración local](docs/05-onboarding.md)
6. [Guía para Windows](docs/06-windows.md)
7. Apoyo: [pase de HU a master](docs/guia-pase-hu-a-master.md), [flujo de ramas Git](docs/guia-git-flujo-ramas.md), [prompt para HU CRUD](docs/prompt-hu-crud-db-be-fe.md)

## Qué debe configurar cada persona

| Qué | Dónde |
|-----|-------|
| Token de Jira | Llavero (`jira-api-token`) |
| Token de Sonar local (User Token `squ_`) | Llavero (`sonar-local-token`) |
| Credenciales JFrog | `~/.gradle/gradle.properties`, `.npmrc` |
| Identidad de git | `git config user.name` / `user.email` |
| Variables locales de cada repo | `env.local` (no versionado) |

Detalle en [docs/05-onboarding.md](docs/05-onboarding.md).

## Cómo contribuir

- Un cambio = una unidad de comportamiento = un commit (Conventional Commits).
- Antes de commitear: `scripts/check-secrets.sh`.
- Nada de datos personales, credenciales, correos ni rutas absolutas de usuario.
- Los aprendizajes nuevos van en `skills/learnings/<nombre>/SKILL.md` con síntoma, causa raíz, procedimiento y qué NO hacer.

## Créditos y licencias

Contenido propio bajo licencia [MIT](LICENSE). Historial de cambios en [CHANGELOG.md](CHANGELOG.md).

Las skills `chained-pr`, `work-unit-commits`, `judgment-day`, `rdd-defect-workflow`, `comment-writer`, `cognitive-doc-design`, `skill-creator`, `skill-improver` y `systemic-issue-triage` provienen del proyecto Gentle AI y conservan su autoría y licencia originales (ver el frontmatter de cada `SKILL.md`).
