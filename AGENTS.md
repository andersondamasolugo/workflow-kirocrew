# Instrucciones para el agente (autoinstalación)

Si un usuario te pasó el link de este repo y te pidió "configurarte" o "instalar el workflow", sigue estos pasos en orden. No hace falta que el usuario haga nada manual salvo pegar sus propios secretos en su llavero.

## 1. Clonar e inspeccionar

1. Clonar el repo en un directorio de trabajo temporal (por ejemplo `$KIROCREW_SCRATCH/workflow-kirocrew` o `~/workplace/workflow-kirocrew`).
2. Leer `README.md` y `docs/05-onboarding.md`.
3. Ejecutar `scripts/check-secrets.sh` para confirmar que el contenido es seguro.

## 2. Instalar

0. Detectar el sistema operativo. En **Windows** seguir `docs/06-windows.md` y usar `powershell -ExecutionPolicy Bypass -File .\install.ps1` (con `-DryRun` primero). En macOS/Linux usar `install.sh`. Los tokens en Windows van en variables de entorno de usuario (`SONAR_TOKEN`, `JIRA_API_TOKEN`), no en el llavero de macOS.
1. Ejecutar `./install.sh --dry-run` y mostrarle al usuario el resumen (cuántos elementos y a qué carpetas va).
2. Ejecutar `./install.sh` (sin `--force`). Si hay archivos existentes que se omitieron, listarlos y preguntar si quiere pisarlos con `--force` (deja backup en `~/.kiro/.gb-backup-<fecha>`).
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

## 4. Workspace (recomendado, opcional)

Pregunta una sola vez si el usuario quiere trabajar por workspace: una carpeta que agrupa los repositorios del proyecto y se abre como directorio de proyecto del chat (equivalente al workspace del IDE). Recomiéndalo si maneja varios repositorios o varias HU; no lo impongas. Si dice que no, continúa sin él.

Si acepta:
1. Pregunta el nombre del proyecto y la ruta. Sugiere una carpeta bajo `~/workplace/` o `~/workspace/` (en Windows `%USERPROFILE%\workplace\`), por la restricción de rutas para subagentes que explica `docs/07-workspace.md`.
2. Ejecuta `scripts/new-workspace.sh <ruta> --dry-run` (en Windows `scripts\new-workspace.ps1 -Path <ruta> -DryRun`) y muestra el resultado. Con su OK, ejecútalo sin `--dry-run`.
3. Si el usuario te da las URL de sus repositorios, agrégalas a `<ruta>/repos.txt` y ejecuta el script con `--clone`. No inventes URL.
4. Indícale cómo usar la carpeta como proyecto del chat (ver `docs/07-workspace.md`) y que el cambio aplica a chats nuevos.

## 5. Verificar y reportar

1. Confirmar que existen `~/.kiro/agents/dev-backend.json`, `~/.kiro/steering/dev-flow-router.md` y `~/.kiro/crew/dev-flows/scripts/sonar_local_gate.py`.
2. Avisar que los agentes, skills y steering se cargan al **iniciar una sesión nueva**: las sesiones ya abiertas no los ven.
3. Entregar un resumen corto: qué se instaló, qué falta configurar y cómo arrancar (pedir una HU por su clave Jira; el router corre `flow-po` primero).

## Si algo falla durante la instalación

No lo ocultes ni reintentes en bucle. Sigue estos pasos para dejar un issue que permita reparar el kit:

1. Guarda la salida del comando que falló en un archivo temporal (por ejemplo `install.log`). Nunca incluyas el contenido de archivos de credenciales.
2. Genera el reporte **sin enviarlo**: `python3 scripts/report_install_issue.py --step "<comando>" --log install.log` (en Windows: `python scripts\report_install_issue.py ...`). El script redacta tokens, correos, el nombre de usuario y la ruta del home.
3. Muestra al usuario el texto completo del reporte y **pídele su OK** antes de publicarlo: el repo es público y el issue lo ve cualquiera.
4. Con el OK, repite el comando agregando `--submit`. Crea el issue en https://github.com/andersondamasolugo/workflow-kirocrew/issues con la etiqueta `install-failure` (evita duplicados por título). Si `gh` no está instalado o autenticado, el script imprime un link pre-llenado para que el usuario lo abra en el navegador.
5. Pasa al usuario el link del issue y continúa con lo que sí se pudo instalar; indica claramente qué quedó pendiente.
6. Si el usuario no autoriza el envío, no publiques nada y deja el reporte en un archivo local para que lo comparta él.

## Reglas al trabajar con este kit

- Seguir `steering/dev-flow-router.md`: nunca commit ni push sin autorización explícita del usuario.
- Mostrar el delta exacto antes de crear un PR y esperar su OK.
- No publicar datos personales ni credenciales en ningún repo.
