---
name: auto/angular-mfe-pr-with-local-only-exclusions
description: Prepara un PR de un microfront Angular excluyendo cambios solo-locales y verifica build/tests/cobertura/Sonar-OWASP por lectura antes de commitear
triggers: crear PR microfront angular, excluir cambios solo-locales, git add selectivo, verificar antes de PR, sonar owasp por lectura, module federation wiring
source: auto
session_key: dashboard:chat-19-1793122883
created_at: 2026-10-28T03:59:11+00:00
---

## When to use
Cuando hay que armar un PR de un microfront/feature Angular (especialmente Module Federation) a develop, con cambios mezclados en el working tree: parte del feature + wiring del MFE + workarounds solo-locales que NO deben llegar al PR. El usuario pide "crear el PR" y suele pedir también tests/cobertura/Sonar/OWASP.

## Steps
1. **Clasificar el `git status --short`** en tres grupos revisando el diff de cada archivo modificado:
   - **Feature nuevo** (carpeta del microfront untracked) → va al PR.
   - **Wiring del MFE** (angular.json, package.json, config-routes, constants, app-routing) → va al PR (es lo que monta el MFE en prod).
   - **Solo-local** (mocks de menú, `historyApiFallback` en webpack dev-server, cualquier bloque marcado "NO COMMITEAR") → NO va al PR.
   Leer el diff de cada archivo dudoso; no asumir por el nombre.
2. **Confirmar que el wiring NO requiere el webpack del shell**: si el shell carga remotes DINÁMICAMENTE (`loadRemoteModule` + `resolveRemoteEntry` + un REMOTE_NAME_MAP/constants en runtime), entonces `shell/webpack.config.js` no necesita cambios para el MFE nuevo → su único diff (`historyApiFallback`) es local. `grep -nE 'remotes|ModuleFederation' projects/shell/webpack.config.js` para verificar que no usa `remotes` estáticos.
3. **Verificar antes de commitear** (en el Mac con swap, un solo microfront es ligero; correr en serie en la sesión principal, no delegar a subagente si RAM TIGHT):
   - Unit tests + cobertura: `npx jest --coverage --testPathPatterns "<microfront>"` → confirmar verde y cobertura propia >80%.
   - Build real con la config de app: `npx ng build <microfront> --configuration=development` → EXIT 0 (usa tsconfig.app.json, no solo specs).
   - Sonar/OWASP NO corren local → revisión por LECTURA del diff con greps: secrets/credenciales (`password|secret|token=|api_key|Authorization:`), `any`/`console`/`debugger`, y accesibilidad S6827 (todo `(click)` debe estar sobre `<button>`/`<a>`; verificar el elemento portador leyendo hacia atrás la etiqueta de apertura, no solo la línea del click).
4. **Staging selectivo** (nunca `git add .`): `git add -n <carpeta-feature>/` primero para listar y chequear que no arrastre basura (node_modules, dist, .kiro, coverage, *.log); luego `git add` de la carpeta del feature + los archivos de wiring uno por uno. Confirmar con `git diff --cached --stat` y que los solo-locales quedan en `^ M` (no staged).
5. **Commit + push + PR en comandos AISLADOS** (evita la safety policy git-publish-floor): confirmar identidad git; `git commit -F -` o `-F <archivo>` (mensaje multilínea por stdin/archivo, NO `-m` multilínea); `git fetch` + verificar que la rama no existe en remoto y HEAD está alineado con develop; `git push -u origin <rama>` como comando único con rama explícita; crear el PR con `gh pr create --base develop --head <rama> --body-file "$KIROCREW_SCRATCH/body.md"` (NO `--body "$(cat <<EOF...)"` porque los backticks internos del markdown rompen el shell). Limpiar el archivo scratch al final.

## Gotchas
- `--body "$(cat <<'EOF'...)"` con backticks de markdown adentro ROMPE el parseo del shell. Escribir el body a `$KIROCREW_SCRATCH/body.md` y usar `--body-file`.
- El filtro `grep -v '<button'` NO excluye clicks cuyo `(click)` está en una línea distinta del `<button`; para S6827 hay que resolver qué etiqueta de apertura porta el atributo leyendo hacia atrás (awk que recuerde el último `<tag` hasta la línea del click).
- Workarounds solo-locales típicos a excluir: mock de menú (fca.mock.ts, menu-permissions.service.ts), `historyApiFallback:true` en el webpack dev-server del shell. Suelen venir marcados "NO COMMITEAR".
- En RAM TIGHT en el Mac (tiene swap): no bloquear ni delegar a subagente para un solo microfront; correr jest/build en serie en la sesión principal.
- Sonar/OWASP reales corren en el CI del PR, no localmente; la verificación local es una revisión por lectura del diff contra las reglas.
