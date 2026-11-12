---
name: auto/sonar-scanner-macos-jre-spawn-fix
description: Fix SonarScanner CLI posix_spawn/Keychain failure on macOS by disabling the embedded JRE, then isolate token-permission errors
triggers: sonar-scanner, posix_spawn failed, Cannot run program security, MacCertificateUtils, Not authorized or project not found, Execute analysis, SonarCloud local analysis
source: auto
session_key: dashboard:chat-23-1793321545
created_at: 2026-10-30T12:53:30+00:00
---

> **Plataforma:** el síntoma A es exclusivo de macOS. En Windows y Linux no aplica; el síntoma B (permisos del token) es idéntico en cualquier sistema. En Windows reemplazá `curl` por `curl.exe` y `export VAR=...` por `$env:VAR="..."`.

## When to use
Running `sonar-scanner` CLI locally on macOS and it fails before uploading, OR it connects but is rejected at `Create analysis`. Two distinct failure classes get confused; this separates them.

## Symptoms and their real causes

### A. `posix_spawn failed` / `Cannot run program "security"` (MacCertificateUtils)
The scanner's **embedded JRE** cannot spawn the macOS `security` binary to read the Keychain for system certs. This is an environment/JRE bug, NOT a config or token problem. `SONAR_SCANNER_OPTS=-Djavax.net.ssl.trustStoreType=JKS` does **not** fix it — scanner 6.x always probes the Keychain first.

### B. `Not authorized or project not found` at `Create analysis`
The scanner connected, authenticated, loaded plugins, processed properties, then the **server** rejected it. This is a **token permission** problem, not environment. A token with only `Browse` can read the quality gate but cannot `Execute analysis` (upload). No container, MCP, or code change bypasses this — the rejection is server-side.

## Steps
1. **For symptom A** — point the launcher at a real system JDK instead of the embedded JRE:
   - Edit `<scanner>/bin/sonar-scanner`, change `use_embedded_jre=true` to `use_embedded_jre=false` (it is hardcoded; the launcher ignores `SONAR_SCANNER_JAVA_HOME` unless this is false).
   - Export `JAVA_HOME` to a full JDK you installed yourself (e.g. Temurin 17), not a sandboxed JRE. A full JDK can spawn `security` and resolve the Keychain.
   - Ensure `/usr/bin` is on PATH: `export PATH="/usr/bin:/bin:$PATH"`.
   - Re-run. Success looks like it progressing past `Communicating with SonarCloud` / `Loading required plugins` / `Process project properties`.
2. **If it now reaches `Create analysis` and fails with `Not authorized`** — this is symptom B, a token scope issue. Diagnose without burning another build:
   - Validate token: `curl -s -u "$TOKEN:" "https://sonarcloud.io/api/authentication/validate"` → expect `{"valid":true}`.
   - Project visible: `curl -s -u "$TOKEN:" "https://sonarcloud.io/api/components/show?component=<projectKey>"` → component object = in scope.
   - Read gate (proves Browse): `curl -s -u "$TOKEN:" "https://sonarcloud.io/api/qualitygates/project_status?projectKey=<projectKey>&branch=<branch>"`.
   - If validate=true, component visible, gate readable, but analysis still fails → token has Browse but lacks `Execute analysis`. Fix: regenerate with Browse+Execute analysis, or use a personal User Token (inherits your user's analysis permission).
3. **To analyze a local branch without polluting shared branch metrics** — run in ephemeral PR mode so SonarCloud treats it as a separate PR analysis:
   `-Dsonar.pullrequest.key=local-<branch> -Dsonar.pullrequest.branch=<branch> -Dsonar.pullrequest.base=<baseBranch>`.
   Never run a plain analysis against the real `develop`/base projectKey from a dev machine — it overwrites the team's dashboard metrics.
4. **To only read the gate** (no compile, no upload), a Browse token + the `project_status` Web API call is enough. This is the zero-risk path when the CI already analyzed the branch.

## Gotchas
- Do NOT reach for Docker/an MCP to fix either symptom. Docker runs the SAME scanner with the SAME token against the SAME server — symptom B reproduces identically. The SonarQube MCP is just the Web API wrapped; read ops work with Browse, analysis still needs Execute analysis.
- `brew install` can fail under a sandboxed shell; install the scanner by tarball with `curl` and `chmod +x bin/* jre/bin/*` after unzip.
- Secrets: pass the token via `${SONAR_TOKEN}` env var, never hardcode in `mcp.json` or any versioned file (CWE-798). SonarQube rule S7791 flags exposed scoped org tokens.
- Effort signal: if the scanner progresses further than before (connects, loads plugins) the environment fix worked — don't keep tweaking SSL/truststore options; shift attention to the token.
- Coverage: run `./gradlew clean test jacocoTestReport` first so `build/reports/jacoco.xml` exists; Sonar reads it for new-code coverage.
