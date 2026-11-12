---
name: auto/sonar-local-docker-gate-setup
description: Set up a local SonarQube Docker server plus scanner to mirror SonarCloud New Code gate on a diff before commit
triggers: sonar local, sonarqube local, sonar-local.properties, local sonar gate, localhost:9000 sonar, mirror sonarcloud locally, sonar scanner setup
source: auto
session_key: dashboard:chat-28-1793800377
created_at: 2026-11-04T17:52:55+00:00
---

## When to use
When you need a local SonarQube (Community, Docker) to reproduce a repo's SonarCloud analysis before pushing — measuring issues, coverage, and duplication on only the lines changed in a diff, so a commit won't fail the CI gate. Works for both frontend (repo root) and backend monorepos (one `*-ms` module at a time).

## Steps
1. **Preflight the host.** `which docker sonar-scanner`, `docker ps -a`, `uname -m` (arch), confirm the target repo path exists and is readable. On a sandboxed shell, Docker install and `docker run` may fail (`sandbox-exec` nesting, `~/.docker/config.json` not permitted) — have the user start the daemon and run the container in their native terminal.
2. **Run the server:** `docker run -d --name sonarqube -p 9000:9000 sonarqube:community`. Poll readiness with `curl -s http://localhost:9000/api/system/status` until it reports `UP`.
3. **Install the scanner** by direct download (NOT Homebrew in a sandbox): fetch the arch-matched `sonar-scanner-cli` zip into a tools dir, unzip, `chmod +x bin/*`. On macOS also `chmod +x jre/bin/*` and `xattr -dr com.apple.quarantine .` — the embedded JRE ships non-executable/quarantined.
4. **Mirror the repo config, don't invent it.** Generate `sonar-local.properties` as a near-exact copy of the committed `sonar-project.properties`, overriding only `sonar.projectKey`/`projectName` (append `-local`) and `sonar.host.url=http://localhost:9000`, and dropping `sonar.organization` (SonarCloud-only). Verify with `diff` that every other key (sources, `coverage.exclusions`, `cpd.exclusions`, `lcov.reportPaths`) is IDENTICAL. Copying the repo file is what makes the local dashboard match SonarCloud.
5. **Keep it out of git:** add `sonar-local.properties` and the scanner work dir to `.git/info/exclude` (local, uncommitted). If `.scannerwork/` is already tracked in some modules, set `sonar.working.directory=.scannerwork-local` so the scan doesn't clobber tracked files. Confirm `git status` stays clean.
6. **Backend monorepo:** one `sonar-local.properties` per `*-ms` module, run the gate once per module the diff touches, after `./gradlew test jacocoTestReport` so compiled classes and `jacoco.xml` exist on disk.
7. **Token:** generate a **User Token** (prefix `squ_`) in My Account → Security, store it in the OS secret store (e.g. macOS Keychain `security add-generic-password -s sonar-local-token -w`), never in chat. An Analysis Token (`sqa_`) only has `scan`/`provisioning` and returns 403 on hotspots.
8. **Run and read:** scan, wait for the server to process, then query the Web API (`/api/issues/search`, `/api/measures/component`, `/api/hotspots/search`, `/api/qualitygates/project_status`) filtered to the diff's lines. Emulate SonarCloud New Code: block only on issues/hotspots/uncovered lines falling inside changed line ranges — new bug, new vulnerability, new Blocker/Critical, new-line coverage <80%, new-code duplication >3%. Report dashboard and issues links.

## Gotchas
- **`posix_spawn failed` / `Cannot run program "security"`** from the scanner on macOS: the embedded JRE can't spawn the Keychain `security` binary. Fix by pointing the launcher at a system JDK: set `use_embedded_jre=false` in `bin/sonar-scanner` and export `JAVA_HOME` (Temurin 17).
- **zsh eats inline `#` comments** on an interactive line, so `npm run x # note` passes the note to the tool as args (`No tests found`). Give commands one per line, no trailing comments.
- **Local ≠ SonarCloud even with identical exclusions:** server-side exclusions set in the UI (Analysis Scope) aren't in the repo file; the Quality Profile is default "Sonar way" not the org's; New Code period differs; the Community analyzer version differs. The CI gate stays authoritative.
- **Stray local `dist/`/`coverage/`** that a clean CI checkout lacks inflate duplication (e.g. `dist/common-lib` duplicating `projects/common-lib`) — exclude them locally.
- **Config is not in git on purpose**, so a fresh clone / worktree / `git clean -fdx` wipes it. Regenerate it with a setup script rather than by hand; keep project keys stable so you don't spawn duplicate projects on the server.
- **Already-open chat sessions** load skills/steering only at startup — anything created today is invisible to them. Promise reusability only for *new* sessions, and put a short pointer in always-loaded steering (a router row) so new sessions distinguish "sonar local" from SonarCloud.

## Equivalentes en Windows (PowerShell)
Los pasos de arriba son los de macOS. En Windows:

| Paso | macOS | Windows |
|------|-------|---------|
| Preflight | `which docker sonar-scanner`, `uname -m` | `Get-Command docker, sonar-scanner`, `$env:PROCESSOR_ARCHITECTURE` |
| Readiness del servidor | `curl -s http://localhost:9000/api/system/status` | `curl.exe -s http://localhost:9000/api/system/status` (con `.exe`, porque `curl` en PowerShell 5 es un alias de `Invoke-WebRequest`) |
| Instalar el scanner | zip + `chmod +x bin/* jre/bin/*` + `xattr -dr com.apple.quarantine .` | Descomprimir el zip de Windows en `%USERPROFILE%\tools\` y agregar `bin` al `PATH`. No hay `chmod` ni cuarentena; si Windows bloquea los archivos descargados, `Get-ChildItem -Recurse | Unblock-File` |
| Excluir de git | `.git/info/exclude` | Igual (`.git\info\exclude`) |
| Token (`squ_`) | Llavero con `security add-generic-password` | Variable de usuario `SONAR_TOKEN` (el script `sonar_local_gate.py` la lee primero) |
| Java 17 | `JAVA_HOME` con `java_home -v 17` | Temurin 17 y `JAVA_HOME` apuntando a su carpeta |

- El fallo `posix_spawn failed` / `Cannot run program "security"` es **exclusivo de macOS** (el JRE embebido no puede lanzar el binario `security` del llavero). En Windows no aplica; si el scanner falla por otra razón, ver `docs/06-windows.md`.
- El gotcha de zsh con comentarios `#` inline no aplica en PowerShell, pero sigue siendo buena práctica un comando por línea.
- Sin verificar en una máquina Windows real: si algo falla, el flujo de reporte de `AGENTS.md` abre un issue.
