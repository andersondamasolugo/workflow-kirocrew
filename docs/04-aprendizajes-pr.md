# Aprendizajes de PR

Lecciones destiladas de PRs reales del proyecto. Cada una tiene su procedimiento detallado en `skills/learnings/`.

## 1. Plantilla obligatoria

Todo PR termina con las dos secciones de `templates/pr-footer.md`: **Relación de Historias de Usuarios** (links Jira) y **Tipos de Cambios** (con `[x]` solo en lo que el PR lleva). El robot de revisión las analiza para saber qué se sube. Copiar las glosas literalmente.

Para el body del PR usar un archivo y `gh pr create --body-file`; pasar el body inline con heredoc se rompe si tiene backticks.

## 2. Una rama mergea limpio solo hacia la rama de la que fue cortada

- El sufijo de la rama (`-to-stage`, `-to-master`), la base del PR y la rama de corte deben coincidir. GitHub propone `develop` por defecto: cambiarlo.
- Verificar antes de abrir el PR:
  ```bash
  git fetch origin
  git merge-tree --write-tree origin/<destino> origin/<rama>; echo $?   # 0 limpio, 1 conflicto
  ```
- Para llevar una HU a un ambiente: rama **fresca** cortada de `origin/<destino>` + `cherry-pick` de **solo** los commits de la HU.
- Un PR `develop → stage` arrastra todo lo que develop tenga adelante. Antes de proponerlo: `gh api repos/<org>/<repo>/compare/stage...develop` y listar qué HUs entrarían.
- Skills: `promote-merged-branch-fresh-pr`, `promote-commits-develop-to-stage-by-patch-id`, `isolate-feature-delta-to-correct-branch`.

## 3. Nunca pushear a la rama de un PR ya mergeado

Verificar `gh pr view <n> --json state,mergedAt`. Si está `MERGED`, el push deja el commit huérfano y no relanza el CI: crear rama fresca desde `origin/<base>` y un PR nuevo.

## 4. Criterios nuevos días después de mergear

No juntar commits viejos (ya públicos) con los nuevos en una rama: reescribe historia pública. Cada tanda es un vehículo independiente: rama fresca de `origin/develop` actualizado → PR a develop; luego rama fresca de `origin/stage` + cherry-pick de solo la tanda nueva → PR a stage. La HU "vive junta" en el ambiente, no en una rama.

## 5. Pase a master con control de cambios

El validador exige que la rama head del PR a master sea `pre`/`stage` o se haya creado desde un **tag válido** sobre un commit que exista en el ambiente previo. Un delta "fabricado" sobre master no tiene linaje y el robot lo rechaza. Alternativa segura sin tocar stage: rama puente cortada de master + cherry-pick de los commits **reales** de la HU que viven en stage. Nivelar stage es destructivo y se hace con las Gestoras de Cambios, no solo. Ver `docs/guia-pase-hu-a-master.md`, `skills/learnings/pass-isolated-fix-to-master-via-sha-validator`.

## 6. Repos de base de datos (DOFI)

Una sola rama con el nombre exacto de la HU, cortada de `master`, con los cambios en **un solo commit**, que recorre develop → stage → master. Sin ramas por ambiente ni sufijos. El PR en DOFI lo crea el desarrollador. BE y FE usan el flujo normal de GitHub, no DOFI.

## 7. Qué hacer con los hallazgos del code review

- Distinguir la fuente con datos duros: `gh pr checks`, `reviewDecision`, `mergeable`.
  - **Policy Engine / Transversal Checks**: es el gate real.
  - **SCA**: vulnerabilidades de dependencias, normalmente preexistentes y ajenas a la HU.
  - **Code Review AI**: advisory, no bloquea; también comenta archivos que están en el árbol pero fuera del diff.
- Antes de tocar nada, `git diff --name-only origin/<base>`: lo que está fuera del diff es de otra HU y no se corrige en este PR.
- Con decenas de sugerencias, clasificar primero (ajeno / falso positivo o estilo / real del código propio / decisión de equipo) y atacar solo lo real, **agrupado por causa raíz**. No es una lista de N tareas.
- Skill: `triage-bulk-code-review-findings`.

## 8. Antes del commit, no después

Correr tests, cobertura, `flow-security-gate` y Sonar local **antes** del commit. El pr-analysis del CI solo corre al abrir/actualizar el PR y no se puede invocar localmente; lo que sí se puede correr antes es el gate de seguridad y Sonar local. Si el cambio toca compilación (DTO, MapStruct, Lombok, entidades), compilar y testear localmente primero: un fallo de compilación barato no debe costar un ciclo de CI.

## 9. Contratos entre servicios

Un DTO cliente que consume un endpoint de otro servicio debe llevar `@JsonIgnoreProperties(ignoreUnknown = true)`. Si no, cuando el productor agrega un campo, la deserialización revienta y, con un fail-open, el síntoma queda escondido hasta QC.

## 10. Spring: trampas frecuentes

- `findBy<Campo>(null)` en Spring Data genera `WHERE col = NULL`: devuelve vacío sin error. Para filtros opcionales, cubrir el caso `null` explícitamente (por ejemplo `findAll(pageable)`).
- Quitar el default de un `@Value` obliga a definir la propiedad en **todos** los perfiles, incluido el `application.yml` de test. Si falla el contexto, caen en cascada muchos tests con la misma cadena de excepciones: la firma de un problema de contexto, no de N tests rotos. Se arregla agregando la clave al yml de test.
- Un `BUILD FAILED` con Lombok sin procesar (`log` o `getX()` inexistentes) en archivos ajenos al diff suele ser del runner: reintentar el run antes de tocar código. Un 429 de Docker Hub en `microservice-template-prepare` es transitorio: `gh run rerun --failed`.

## 11. Archivos locales que no se suben

Para blindar archivos solo-locales (por ejemplo una `LocalSecurityConfig`), usar `.git/info/exclude`, no el `.gitignore` versionado, y comprobar con `git check-ignore`. Ver `angular-mfe-pr-with-local-only-exclusions`.

Cuidado con `git rm -r --cached .kiro`: saca del índice toda la carpeta ya trackeada, no solo lo nuevo. Para quitar solo lo propio: `git reset --soft HEAD~1`, des-stagear rutas específicas y recommitear.

## 12. Higiene de commits

- `git add` explícito, nunca `git add .`. Verificar con `git diff --cached --stat`.
- Aislar el delta con `git stash -u` + checkout selectivo cuando el working tree mezcla fix, workaround local y archivos ajenos.
- Si un cherry-pick choca porque la rama destino ya reestructuró los mismos archivos, abortar y **re-aplicar** a mano sobre la estructura nueva.
- `git commit` y `git push` como comandos separados, con rama explícita; para borrar ramas remotas, un `git push origin --delete <rama>` por cada una.
