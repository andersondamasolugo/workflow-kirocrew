# Guía para Windows

El kit funciona en Kiro Crew para Windows. La instalación y la configuración local cambian en estos puntos.

> Estado de verificación: el instalador `install.ps1` y esta guía se escribieron a partir de la documentación de Kiro Crew y de los scripts del kit. **No se probaron todavía en una máquina Windows.** Si algo falla, abre un issue o corrige el script y sube el cambio.

## Qué dice la documentación de Kiro Crew sobre Windows

- Plataformas soportadas: macOS, Linux y Windows. En Windows, Kiro Crew corre de forma nativa desde una instalación Python y se lanza con `python -m kiro_crew gateway`.
- El gateway de Windows **no se actualiza solo**: hay que actualizarlo a mano.
- El shell por defecto es **PowerShell** (`$env:VAR="valor"`, `Set-Location`, `.\gradlew.bat`). Los comandos con `export`, `rm -rf` o `cd /d` de macOS no aplican.
- Los archivos de skills y prompts deben ser **UTF-8**. Un archivo guardado como UTF-16 (el default de las redirecciones `>` de PowerShell 5) se ignora. Si editas a mano, guarda en UTF-8.
- Los hooks usan `%ComSpec% /c` en lugar de `/bin/sh -c`.

## 1. Instalar el kit

Pega en un chat de Kiro Crew el mismo mensaje del README. Kiro detecta Windows y usa `install.ps1`. También puedes hacerlo a mano:

```powershell
git clone https://github.com/andersondamasolugo/workflow-kirocrew.git
Set-Location workflow-kirocrew
powershell -ExecutionPolicy Bypass -File .\install.ps1 -DryRun   # ver qué copiaría
powershell -ExecutionPolicy Bypass -File .\install.ps1           # instalar; no pisa existentes
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Force    # pisar, con backup
```

Destino: `%USERPROFILE%\.kiro\` (o `%KIRO_HOME%` si la defines). La estructura es la misma que en macOS.

`scripts/check-secrets.sh` es un script bash: en Windows córrelo desde Git Bash, o omite ese paso si solo estás instalando.

## 2. Configuración local en Windows

| Qué | macOS | Windows |
|-----|-------|---------|
| Token de Sonar local | Llavero (`sonar-local-token`) | Variable de entorno de usuario `SONAR_TOKEN` |
| Token de Jira | Llavero (`jira-api-token`) | Variable de entorno de usuario `JIRA_API_TOKEN` |
| Credenciales JFrog | `~/.gradle/gradle.properties`, `.npmrc` | `%USERPROFILE%\.gradle\gradle.properties`, `%USERPROFILE%\.npmrc` |
| Docker | Docker Desktop | Docker Desktop (WSL2) |
| Java 17 | `java_home -v 17` | Instalar Temurin 17 y definir `JAVA_HOME` |

Para guardar un token como variable de usuario (lo escribes tú en tu terminal, nunca en el chat):

```powershell
$t = Read-Host "Token de Sonar" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($t))
[Environment]::SetEnvironmentVariable("SONAR_TOKEN", $plain, "User")
```

Cierra y reabre Kiro Crew para que herede la variable.

## 3. Sonar local en Windows

El script `dev-flows/scripts/sonar_local_gate.py` lee `SONAR_TOKEN` primero, así que no necesita el llavero. Se ajustó para no depender de `/usr/libexec/java_home` y para encontrar `sonar-scanner.bat`.

```powershell
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
python dev-flows\scripts\sonar_local_setup.py C:\ruta\al\repo
python dev-flows\scripts\sonar_local_gate.py C:\ruta\al\repo --base origin/develop
```

- Descomprime el SonarScanner CLI en `%USERPROFILE%\tools\` o agrégalo al `PATH`.
- El flujo, el veredicto y los umbrales son los de [docs/03-sonar-local.md](03-sonar-local.md).
- Los pasos de ese documento que mencionan `security add-generic-password`, `chmod` y `.zshrc` son de macOS; no los uses en Windows.

## 4. Diferencias que conviene conocer

- **Rutas largas:** si `git` o `gradlew` fallan por rutas largas, activa `git config --global core.longpaths true`.
- **Fin de línea:** `git config --global core.autocrlf true` evita diferencias falsas en el diff.
- **Scratch:** Kiro Crew guarda el espacio temporal en `C:` por defecto y puede crecer; se puede mover con `KIROCREW_SCRATCH_ROOT` (solo Windows).
- **Aprendizajes con comandos macOS:** las skills de `skills/learnings/` que usaban llavero, `chmod`/`xattr` o rutas de macOS ahora llevan una sección "Equivalentes en Windows" (Jira, Sonar local, E2E con playwright-cli, Oracle MCP). Siguen sin verificarse en una máquina Windows real.
- **Scripts portables:** `dev-flows/scripts/read_secret.py` (lee un secreto de la variable de entorno o del almacén del sistema) y `dev-flows/scripts/jira_read.py` (lee issues de Jira por REST con `JIRA_SITE`, `JIRA_EMAIL` y `JIRA_API_TOKEN`) funcionan igual en Windows, macOS y Linux.
