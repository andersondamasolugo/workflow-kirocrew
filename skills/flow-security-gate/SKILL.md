---
name: flow-security-gate
description: Gate de seguridad OWASP pre-commit, nativo KiroCrew. Corre ANTES de cada commit sobre el diff staged, clasifica hallazgos con las skills secure-coding / secure-coding-java / secure-coding-frontend según el stack, DELEGA la reparación al agente especializado (dev-backend / dev-front-tienda / dev-front-bolivar-ui), re-audita y BLOQUEA el commit hasta que no queden hallazgos Critical/High. Úsalo en el paso Commit del pipeline de una HU.
always: false
triggers: flow-security-gate, security gate pre-commit, gate de seguridad, revisar seguridad antes de commit, owasp pre-commit, repara hallazgos de seguridad
---

# flow-security-gate — gate OWASP pre-commit con reparación delegada

> ## 🎫 Flujo activo — SECURITY GATE (pre-commit)
> | Campo | Valor |
> |-------|-------|
> | **Flujo** | `flow-security-gate` |
> | **Tipo** | Gate de seguridad OWASP sobre el diff staged, ANTES del commit |
> | **Conocimiento** | `secure-coding` (general) + `secure-coding-java` + `secure-coding-frontend` |
> | **Reparación** | DELEGA al agente del stack: `dev-backend` (Java/Spring), `dev-front-tienda`/`dev-front-bolivar-ui` (Angular) |
> | **Fases** | Stage diff → Clasificar stack → Auditar OWASP → Reparar (delegada) → Re-auditar → Veredicto |
> | **Bloqueo** | NO se commitea hasta que no queden hallazgos **Critical/High** |
> | **NO hace** | El commit mismo (lo hace el flujo dueño, con la regla de autorización) |
> | **Cierre** | `GATE: CLEAN` (commit permitido) o `GATE: BLOCKED` (hallazgos abiertos) |
>
> **Al iniciar el flujo, emite este banner** para que sea evidente qué flujo corre.

Flujo nativo KiroCrew. Es la **capa de seguridad gemela del hook de calidad pre-commit**
(tests + cobertura + Sonar/OWASP por lectura). Corre en el paso **Commit** del pipeline de
una HU (`dev-flow-router.md`), DESPUÉS de implementar + unit tests y ANTES de que el flujo
dueño haga el `git commit`.

> **Enforcement — qué garantiza y qué no (honesto).** KiroCrew NO instala un `.git/hooks/pre-commit`
> ejecutable: este gate es una **regla de comportamiento del agente** (como el hook de calidad ya
> guardado vía `learn_add`). El agente está OBLIGADO por la regla a correr este gate y a no commitear
> con hallazgos Critical/High abiertos. El enforcement DURO adicional lo da el gate de CI real
> (Sonar Blocker/Critical, OWASP del pipeline). Este gate adelanta esos hallazgos al momento del
> commit para no perder el round-trip con el CI.

## Fases

1. **Stage diff** — obtén EXACTAMENTE lo que se va a commitear:
   `git diff --staged` (si no hay nada staged, `git diff` del working tree y avisa que audita
   el working tree, no el stage). Solo el diff — nunca todo el repo. Lista los archivos tocados
   con `git diff --staged --name-only`.

2. **Clasificar stack** — por las extensiones de los archivos del diff, decide qué skills cargar
   (una o varias; un micromonolito puede tocar los dos):
   - `.java` / `application*.yml` / `pom.xml` / `build.gradle` → `secure-coding` + `secure-coding-java`, reparador `dev-backend`.
   - `.ts` / `.html` / `.scss` / `angular.json` / `package.json` (Angular/React) → `secure-coding` + `secure-coding-frontend`, reparador `dev-front-tienda` (`td-*`/PrimeNG) o `dev-front-bolivar-ui` (`sb-ui-*`) según el design system del repo.
   - `.py` / otro → `secure-coding` (general), reparador `dev-backend`.
   Carga las skills con `skill_search(action='read', key=...)` y usa sus reglas A01–A10.

3. **Auditar OWASP (read-only)** — sobre el diff, aplica las reglas de las skills cargadas.
   Respeta sus EXCEPCIONES explícitas (auth transversal ya implementada, gating por perfil que
   excluye prod, nivel de log efectivo, source maps resueltos a prod). Por cada hallazgo real:
   `[SEC-NNN] <categoría OWASP> — <SEVERIDAD>` + `archivo:línea` + evidencia + riesgo en negocio +
   remediación concreta. Nunca pegues un secreto en claro: refiérete por nombre de clave.
   > **Ataca la raíz, no el síntoma (regla 8 del router).** Verifica el hallazgo contra el código
   > real antes de proponer fix; varios hallazgos con la misma causa = UN fix en la raíz. No entres
   > en el loop de parchear cada sugerencia: el mecanismo que afirma el hallazgo es hipótesis, solo
   > el síntoma es evidencia.

3b. **Medir con SonarQube local (si está disponible)** — complementa la lectura de la fase 3 con
   una medición real. Corre:
   `python3 ~/.kiro/crew/dev-flows/scripts/sonar_local_gate.py <repo> --base origin/<rama-base>`
   - Requisitos: contenedor `sonarqube` arriba (`localhost:9000`), `sonar-local.properties` en la
     raíz del repo (copia de `sonar-project.properties` con host/projectKey locales, excluido vía
     `.git/info/exclude`, NUNCA commiteado) y token en el Keychain `sonar-local-token`.
   - Evalúa las LÍNEAS CAMBIADAS como el New Code de SonarCloud. `SONAR-LOCAL: BLOCKED` si en
     código nuevo hay: cualquier BUG o VULNERABILITY (tumba Reliability/Security A), cualquier
     issue BLOCKER/CRITICAL o impacto HIGH/BLOCKER (complejidad S3776, accesibilidad S1082/S6827),
     un hotspot por revisar, cobertura de líneas nuevas < 80% o duplicación de líneas nuevas > 3%.
     Cada causa entra a la fase 4 como hallazgo a reparar con su `archivo:línea` (el script lista
     las líneas sin cubrir). Los code smells menores salen como `WARN` (corrígelos si son baratos)
     y los issues preexistentes fuera de las líneas cambiadas como `info` (no los toques).
   - **Reportar SIEMPRE el link al usuario**: en la respuesta de cada análisis pega el
     `dashboard:` y el `issues:` que imprime el script como links markdown, más el link
     individual de cada `BLOCK`. Sin link no está reportado.
   - **Arreglar ANTES de commitear, sin pedir permiso**: un `BLOCKED` significa que el PR fallaría
     en SonarCloud y subirlo no tiene sentido. Repara en el loop fases 4→5 (re-corre el gate tras
     el fix, recompilando/regenerando cobertura) hasta `SONAR-LOCAL: CLEAN`, con el mismo máximo
     de 3 iteraciones. Solo si a la 3ª sigue `BLOCKED`, o el fix exige una decisión de producto,
     escala al usuario con los links; nunca commitees con el gate en `BLOCKED`.
   - `SONAR-LOCAL: SKIPPED` (server caído, sin token, sin config, scan fallido) NO bloquea:
     decláralo y quédate con la revisión por lectura de la fase 3. Nunca levantes el contenedor
     ni generes el token por iniciativa propia.
   - Es pesado (minutos, ~2 GB): córrelo UNA vez por entrega antes del commit, no por edición. En
     la re-auditoría (fase 5) vuelve a correrlo solo si la reparación tocó archivos que tenían
     issues medidos. Sigue siendo una aproximación: el perfil local es "Sonar way", no el de la
     organización; el gate real es SonarCloud en el CI.
   - **Backend (monorepo de microservicios, p. ej. `san-andres-autorizaciones-ms`)**: cada módulo
     `*-ms` es su propio proyecto Sonar con su propio `sonar-local.properties`. Pasa el
     DIRECTORIO DEL MÓDULO (no la raíz del repo) y córrelo una vez por cada módulo que toque el
     diff (`git diff --name-only <base>...HEAD | cut -d/ -f1 | sort -u`); el script hace las rutas
     del diff relativas al módulo. Requiere clases compiladas y `build/reports/jacoco.xml`
     ACTUALES: corre antes `./gradlew test jacocoTestReport` del módulo (ya es parte del hook de
     calidad), si no Sonar mide binarios/cobertura viejos. Los configs locales usan
     `sonar.working.directory=.scannerwork-local` porque `.scannerwork/` está trackeado en git en
     algunos módulos: no lo cambies ni commitees nada de `.scannerwork*`.

4. **Reparar (DELEGADA al agente especializado)** — SOLO los hallazgos **Critical/High** bloquean
   y deben repararse; Medium/Low se listan como informativos y NO bloquean (coherente con regla 8).
   Entrega la reparación al agente del stack (del paso 2):
   - **Con RAM y `spawn_run` disponible** (`cwd` hijo directo de un root permitido): un task por
     stack con los hallazgos Critical/High, su `archivo:línea` y la remediación propuesta. El
     subagente REPARA en el código, no solo describe. `include_lessons=true`, `include_project=true`.
   - **Host tight / spawn rechazado / Mac con swap donde el usuario pidió correr igual**: repara
     INLINE en la sesión principal siguiendo la remediación de la skill del stack. Decláralo.
   Un hallazgo = un cambio atómico dirigido a su `archivo:línea`; no toques código fuera del diff.

5. **Re-auditar** — vuelve a correr la fase 3 sobre el diff YA reparado (re-stage si hiciste
   cambios: `git add` de los archivos tocados). Repite Reparar→Re-auditar hasta que no queden
   Critical/High, con un máximo de **3 iteraciones**. Si a la 3ª aún quedan Critical/High,
   el veredicto es `GATE: BLOCKED` y escala a decisión humana — NO commitees.

6. **Veredicto** — última línea exactamente una de:
   - `GATE: CLEAN` — sin Critical/High abiertos. El flujo dueño puede proceder al commit
     (siempre con la regla de autorización: mostrar delta y esperar OK antes del PR).
   - `GATE: BLOCKED` — quedan Critical/High (o se agotaron las 3 iteraciones). NO se commitea;
     lista los hallazgos abiertos y qué falta.

## Orquestación de agentes (spawn_run nativo)
El gate es secuencial (auditar → reparar → re-auditar es un loop dependiente), NO fan-out.
`spawn_run` SOLO para la fase 4 cuando el diff toca DOS stacks independientes (FE + BE en un
micromonolito) y hay RAM: un task por stack, superficies de edición disjuntas. En un Mac con swap
NO bloquees por RAM (hay swap: los spawns se encolan, no se rechazan); si un spawn se
rechaza por `cwd`, repara inline. Nunca entregues el requerimiento entero a un solo worker para
esperarlo y repetir su respuesta.

## Relación con los otros gates
- Es la **capa de seguridad** del commit; el **hook de calidad** (tests + cobertura + Sonar por
  lectura) es la capa gemela. Ambos corren en el paso Commit, ANTES del `git commit`.
- Reutiliza el conocimiento de `flow-audit-security` (veredicto OWASP read-only) pero AÑADE la
  reparación delegada + el loop de bloqueo. `flow-audit-security` es el nodo read-only de un
  workflow; `flow-security-gate` es el gate accionable pre-commit.

## Deliver gate — evidencia por fase (obligatorio, nativo)

Antes de declarar este flujo TERMINADO, vuelve a leer este mismo `SKILL.md` y, por CADA
fase que define arriba, emite una fila en esta tabla:

| Fase | Herramienta/comando ejecutado | Resultado (evidencia real) |
|------|-------------------------------|----------------------------|

Reglas del gate:
- Una fase SOLO cuenta como hecha si pegas la **evidencia real** de haberla ejecutado
  (salida del comando / diff reparado, no una afirmación). Sin evidencia = NO hecha.
- El veredicto `GATE: CLEAN`/`GATE: BLOCKED` debe respaldarse con el diff real auditado y, si hubo
  reparación, con el diff del fix (muestra `git diff --staged --stat`).
- Si no hay diff que auditar, decláralo **BLOCKED** con el motivo — nunca `CLEAN` "a ojo".
- No puedes emitir `GATE: CLEAN` ni permitir el commit con un hallazgo Critical/High abierto.
- Este gate es la fase final y se aplica a sí mismo: es parte del flujo, no un extra opcional.
