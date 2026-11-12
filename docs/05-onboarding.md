# Onboarding y configuración local

## 1. Instalar el kit

```bash
./install.sh --dry-run
./install.sh
```

Destinos (puede variar según tu instalación de Kiro Crew):

| Origen | Destino |
|--------|---------|
| `agents/<n>/agent.json` | `~/.kiro/agents/<n>.json` |
| `agents/<n>/prompt.md` | `~/.kiro/crew/agents/<n>/prompt.md` |
| `agents/judgment-day/*.md` | `~/.kiro/agents/` |
| `skills/flow-*`, `secure-coding*`, `sonar-local-gate`, `spec-*`, `agent-authoring`, `five-whys`, `learnings/*` | `~/.kiro/crew/skills/` |
| Skills de colaboración (`chained-pr`, `work-unit-commits`, `judgment-day`, etc.) | `~/.kiro/skills/` |
| `steering/` | `~/.kiro/steering/` |
| `dev-flows/` | `~/.kiro/crew/dev-flows/` |

## 2. Lo que debés configurar vos (nada de esto viaja en el repo)

| Qué | Dónde | Notas |
|-----|-------|-------|
| Token de Jira | Llavero (`jira-api-token`) o variable `JIRA_API_TOKEN` | Generalo en tu perfil de Atlassian. Ver `skills/learnings/jira-rest-via-keychain-python` |
| Correo de Jira | Tu config local | Reemplazá `<tu-correo>@segurosbolivar.com` en el bloque MCP de `agents/dev-po/prompt.md` solo en tu copia instalada |
| Token de Sonar local | Llavero (`sonar-local-token`) | User Token `squ_`. Ver `docs/03-sonar-local.md` |
| Credenciales JFrog | `~/.gradle/gradle.properties`, `.npmrc` | Necesarias para que `gradlew` resuelva dependencias desde terminal |
| Credenciales de BD / Cognito / env local | `env.local` de cada repo (no versionado) | Nunca las pegues en el chat ni en el repo |
| Git identity | `git config user.name / user.email` | Usá tu identidad real |

Si pegás una credencial viva en un chat, revocala y generá otra.

## 3. Primer uso

1. Abrí el repo de trabajo (FE, BE o DB) y pedí la HU por su clave Jira: el router corre `flow-po` primero.
2. Si es APROBADA, se encadena el flujo del stack (`flow-backend`, `flow-frontend`, …).
3. Antes del primer commit, montá Sonar local (`docs/03-sonar-local.md`).
4. Al abrir el PR, usá `templates/pr-footer.md`.

## 4. Convenciones del kit

- Artefactos técnicos (código, comentarios, commits, PRs) en inglés salvo que el proyecto ya use español. Los documentos de este kit están en español.
- Conventional Commits que expliquen el resultado, no la lista de archivos.
- Sin Co-Authored-By ni atribución de IA en los commits.

## 5. Agregar o cambiar un agente/flujo

Se hace con el agente `dev-flow-architect` y el skill `agent-authoring`. Cada agente = su `prompt.md` (rol) + el `skill://` de su flujo. Tipo de flujo nuevo = una fila en `steering/dev-flow-router.md` + un skill `flow-*`.

## 6. Contribuir al kit

Antes de cada commit:

```bash
scripts/check-secrets.sh
```
