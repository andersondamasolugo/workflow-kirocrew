# Instrucciones para el agente (autoinstalación)

Si un usuario te pasó el link de este repo y te pidió "configurarte" o "instalar el workflow", seguí estos pasos en orden. No hace falta que el usuario haga nada manual salvo pegar sus propios secretos en su llavero.

## 1. Clonar e inspeccionar

1. Clonar el repo en un directorio de trabajo temporal (por ejemplo `$KIROCREW_SCRATCH/workflow-kirocrew` o `~/workplace/workflow-kirocrew`).
2. Leer `README.md` y `docs/05-onboarding.md`.
3. Ejecutar `scripts/check-secrets.sh` para confirmar que el contenido es seguro.

## 2. Instalar

1. Ejecutar `./install.sh --dry-run` y mostrarle al usuario el resumen (cuántos elementos y a qué carpetas va).
2. Ejecutar `./install.sh` (sin `--force`). Si hay archivos existentes que se saltearon, listarlos y preguntar si quiere pisarlos con `--force` (deja backup en `~/.kiro/.gb-backup-<fecha>`).
3. Nunca modificar ni borrar la configuración personal del usuario (su memoria, lecciones, persona, `settings/mcp.json`) ni tocar tokens existentes.

## 3. Configuración local (la hace cada persona; no viaja en el repo)

Preguntar una sola vez qué quiere configurar y guiarlo. Nunca pedirle que pegue un secreto en el chat; que lo escriba en su terminal.

| Qué | Cómo |
|-----|------|
| Jira | Token en el llavero (`jira-api-token`) y su correo corporativo en su MCP local. Ver `skills/learnings/jira-rest-via-keychain-python` |
| Sonar local | `docs/03-sonar-local.md` (Docker + scanner + token `squ_` en el llavero `sonar-local-token`) |
| JFrog | `~/.gradle/gradle.properties` y `.npmrc` con sus credenciales |
| Git | `git config user.name` y `user.email` con su identidad real; no inventar una |

Si el usuario pega una credencial viva en el chat, avisarle que quedó expuesta, no repetirla y recomendar revocarla.

## 4. Verificar y reportar

1. Confirmar que existen `~/.kiro/agents/dev-backend.json`, `~/.kiro/steering/dev-flow-router.md` y `~/.kiro/crew/dev-flows/scripts/sonar_local_gate.py`.
2. Avisar que los agentes, skills y steering se cargan al **iniciar una sesión nueva**: las sesiones ya abiertas no los ven.
3. Entregar un resumen corto: qué se instaló, qué falta configurar y cómo arrancar (pedir una HU por su clave Jira; el router corre `flow-po` primero).

## Reglas al trabajar con este kit

- Seguir `steering/dev-flow-router.md`: nunca commit ni push sin autorización explícita del usuario.
- Mostrar el delta exacto antes de crear un PR y esperar su OK.
- No publicar datos personales ni credenciales en ningún repo.
