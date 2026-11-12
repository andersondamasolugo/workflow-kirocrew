---
name: auto/find-failing-test-from-gradle-ci-run
description: Identifica el test exacto que rompió un CI de Gradle cuando el log solo dice 'N tests, 1 failed' sin el nombre
triggers: gradle CI 1 failed sin nombre, Task :test FAILED, gh run view log-failed, WantedButNotInvoked, test fallido CI, buscar test que rompio el build
source: auto
session_key: dashboard:chat-10-1792594700
created_at: 2026-10-21T16:20:28+00:00
---

## When to use
Un CI de Gradle (GitHub Actions) reporta `BUILD FAILED` con `> Task :test FAILED` y una línea tipo `N tests completed, 1 failed`, pero el log pegado NO dice qué test ni la causa. Necesitas el nombre exacto del método fallido y el assert/excepción para arreglarlo.

## Steps
1. **Confirma el repo/módulo**: el error dice la ruta del report (`.../<modulo>/build/reports/tests/test/index.html`); el `<modulo>` es el subproyecto Gradle que corrió. Verifica el remote local con `git -C <repo> remote get-url origin`.
2. **NO confíes en los `TEST-*.xml` locales** si son de una corrida vieja; lo autoritativo es el run del CI que te pasaron.
3. **Trae el log del CI del run** (requiere `gh` autenticado) y vuélcalo a archivo para poder grepearlo sin re-descargar:
   ```
   gh run view <RUN_ID> --log-failed > "$KIROCREW_SCRATCH/ci-failed.log"
   ```
4. **Aísla la línea del test fallido**. En Gradle el patrón es `ClassName > methodName() FAILED`. Filtra excluyendo el ruido genérico:
   ```
   grep -nE "> .+ FAILED" ci-failed.log | grep -ivE "BUILD FAILED|Task :"
   ```
   Eso da `Clase > metodo() FAILED` + el número de línea en el log.
5. **Lee el contexto del assert** alrededor de esa línea (`sed -n 'START,ENDp' ci-failed.log`): ahí aparece la excepción real (ej. `org.mockito.exceptions.verification.WantedButNotInvoked at FooTest.java:121`, `AssertionError`, `Expected/Actual`) y el archivo:línea del test.
6. **Decide test-vs-código**: abre el test en esa línea y el código de producción que ejercita. Un `WantedButNotInvoked` suele ser desajuste test↔impl (el test espera una interacción que el código no hace). Mira los tests hermanos del mismo archivo para inferir el contrato correcto, y `git log -5 -- <test>` + `<impl>` / `git show <commit>` para ver si ambos cambiaron en el mismo commit (test y código desincronizados).

## Gotchas
- `--log-failed` puede traer logs ruidosos con timestamps ISO al inicio de cada línea; para leer limpio: `sed -E 's/^.*[0-9]{4}-..-..T[0-9:.]+Z //'`.
- Un grep amplio por `FAILED|Expected|Caused by` suele salir ruidoso (Hikari/Shutdown/SchemaDropper); filtra primero por el patrón estructural `> .+ FAILED`.
- `1 failed` de 1800+ no implica bug de runtime: muy a menudo es un test desalineado con la impl que viene así desde el commit que mergeó la HU. Verifica el commit antes de 'arreglar' a ciegas.
- Antes de tocar código, confirma que el test/archivo está en el diff de tu propia HU (git log/show) para no arreglar código ajeno.
