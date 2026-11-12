---
name: sonar-local-gate
description: SonarQube local (Docker) + SonarScanner en el Mac del desarrollador para medir Sonar ANTES del commit en los repos san-andres FE/BE, con configs locales no versionadas que copian las exclusiones de SonarCloud. Cubre setup, regeneración, ejecución del gate y troubleshooting.
triggers: sonar local, sonarqube local, sonar-scanner, sonar-gate, sonar-setup, sonar-local.properties, gate sonar, medir sonar antes del commit, localhost:9000, quality gate local
---

# sonar-local-gate — SonarQube local como gate pre-commit

## Qué existe (estado montado el 2026-11-04)

| Pieza | Dónde / valor |
|-------|---------------|
| Servidor | Contenedor Docker `sonarqube` (imagen `sonarqube:community`, v26.10) en `http://localhost:9000` |
| Docker CLI | `/Applications/Docker.app/Contents/Resources/bin/docker` (no está en el PATH del agente) |
| Scanner | `~/tools/sonar-scanner-7.1.0.4889-macosx-aarch64/bin` (en PATH vía `~/.zshrc`) |
| Token | Keychain `sonar-local-token` (User Token, prefijo `squ_`). El agente lo lee con `security find-generic-password -s sonar-local-token -w`; NUNCA imprimirlo |
| Gate | `~/.kiro/crew/dev-flows/scripts/sonar_local_gate.py <dir> [--base <ref>] [--no-scan]` |
| Setup | `~/.kiro/crew/dev-flows/scripts/sonar_local_setup.py <repo>` |
| Atajos zsh (usuario) | `sonar-setup <repo>`, `sonar-gate <dir> [base=origin/develop]` |
| Integración | Fase 3b de `flow-security-gate` + regla del hook de calidad pre-commit |
| Manual Windows | `~/Desktop/manual.md` (versión PowerShell para terceros) |

## Configs locales (no versionadas)

- `sonar-local.properties` junto a cada `sonar-project.properties`: copia EXACTA de las settings
  de análisis (sources, exclusions, coverage/cpd exclusions, lcov/jacoco) con identidad local:
  `sonar.projectKey=<repo>[-<modulo>]-local`, `sonar.host.url=http://localhost:9000`, sin
  `sonar.organization`, y `sonar.working.directory=.scannerwork-local`.
- Excluidos en `.git/info/exclude` (`sonar-local.properties`, `.scannerwork-local/`), NO en
  `.gitignore`. Nunca commitearlos ni tocar el `sonar-project.properties` del equipo.
- Se pierden con clon nuevo / worktree / `git clean -fdx` → regenerar con `sonar_local_setup.py`.
  Re-correrlo tras un pull que cambie exclusiones en develop.
- FE `san-andres-autorizaciones-frontend`: un config en la raíz.
- BE `san-andres-autorizaciones-ms`: un config POR MÓDULO `*-ms` (9). `.scannerwork/` está
  TRACKEADO en git en `autorizaciones-arl-ms` y `autorizaciones-salud-ms`: por eso el working
  dir local separado.

## Correr el gate

1. Server arriba: `docker start sonarqube` (si está caído el gate da SKIPPED). El agente NO
   levanta el contenedor ni crea tokens por iniciativa propia.
2. FE: `sonar_local_gate.py <repo-FE> --base origin/<base>`.
3. BE: primero `./gradlew test jacocoTestReport` del módulo (Sonar mide los `.class` y el
   `jacoco.xml` que haya en disco); luego `sonar_local_gate.py <repo-BE>/<modulo> --base ...`,
   una vez por módulo tocado (`git diff --name-only <base>...HEAD | cut -d/ -f1 | sort -u`).
4. Veredicto (última línea), evaluado sobre las LÍNEAS CAMBIADAS como el New Code de SonarCloud:
   `SONAR-LOCAL: CLEAN` (exit 0) / `BLOCKED` (exit 1: BUG o VULNERABILITY nuevo, issue
   BLOCKER/CRITICAL o impacto HIGH/BLOCKER nuevo, hotspot por revisar en línea nueva, cobertura
   de líneas nuevas < 80% o duplicación de líneas nuevas > 3%; la línea `reason:` dice cuál) /
   `SKIPPED` (exit 2: server, token, config o scan → caer a revisión Sonar por lectura).
   `WARN` = code smell menor nuevo; `info` = issue preexistente fuera de las líneas cambiadas.
   Cobertura/duplicación salen de `api/sources/lines` (lineHits/duplicated por línea): cuenta
   solo líneas, no condiciones, así que es aproximada.
5. **Siempre**: pegar al usuario el `dashboard:` y el `issues:` del script como links markdown
   (y el link de cada `BLOCK`). **Si da BLOCKED, arreglarlo ANTES del commit sin pedir permiso**
   (reparar → recompilar/cobertura → re-correr el gate) hasta CLEAN, máx. 3 iteraciones; recién
   ahí escalar al usuario. Nunca commitear con BLOCKED: subirlo solo garantiza que falle el CI.
6. Una vez por entrega antes del commit, no por edición (minutos, ~2 GB RAM; el Mac tiene swap,
   no bloquear por RAM). Tiempos medidos: FE 66 s, módulo BE ya compilado 18 s.
7. `--no-scan` reutiliza el último análisis (rápido, para re-filtrar contra otro diff).

## Troubleshooting verificado

- `Cannot run program "security": posix_spawn failed` (MacCertificateUtils): el JRE embebido no
  puede lanzar `security`. Fix aplicado: `use_embedded_jre=false` en `bin/sonar-scanner` +
  `JAVA_HOME=$(/usr/libexec/java_home -v 17)` (Temurin 17). Ver skill
  `auto/sonar-scanner-macos-jre-spawn-fix`.
- `Permission denied` / `Could not find 'java'` tras descomprimir: `chmod +x bin/* jre/bin/*`.
- Hotspots `403 Insufficient privileges`: el token es Analysis Token (`sqa_` global / `sqp_`
  proyecto). Hace falta **User Token** (`squ_`). Comprobar el prefijo sin imprimir el token.
- `npm run test:coverage` "No tests found": no pasar comentarios `# ...` inline en zsh, npm los
  manda a jest como patrón.
- Diff vacío (`SKIPPED: empty diff`): la rama ya está mergeada en la base; usar `--base HEAD~N`.
- Duplicados falsos de `dist/` o `coverage/` en FE: existen local y no en el CI.
- `python3` del sistema es 3.9: los scripts usan `from __future__ import annotations`.

## Límites (decirlos siempre)

Aproximación, no el gate real: el perfil local es "Sonar way", no el de la organización
`segurosbolivar`; SonarCloud puede tener exclusiones de servidor que no están en el repo; el
New Code local difiere. El gate definitivo es SonarCloud en el CI del PR.
