---
name: auto/record-e2e-playwright-cli-shadow-dom-gateway
description: Graba un recorrido E2E con video en playwright-cli dentro de un gateway confinado (sin display, sandbox bloqueado)
triggers: playwright-cli, grabar video E2E, web components shadow DOM, sb-ui, Target crashed sandbox, navegacion menu micro-frontend, evidencia publicable pruebas, Target crashed, sandbox initialization failed, PWTEST_SOCKETS_DIR, recordVideo webm, --no-sandbox
source: auto
session_key: dashboard:chat-3-1792441022
created_at: 2026-10-27T21:53:41+00:00
version: 2
---

## When to use
Cuando el usuario pide grabar un recorrido E2E con video/screenshots publicables (video `.webm`) usando `playwright-cli` desde un gateway/entorno confinado sin display real (ej. el Mac de un gateway KiroCrew), especialmente contra una SPA/micro-frontend con Web Components en shadow DOM. El `browser` MCP tool del panel NO sirve aquí: renderiza en vivo para que el usuario mire, pero NO persiste archivos a disco y su snapshot NO penetra el shadow DOM de componentes tipo `sb-ui-*` (no ves los refs del menú, los clicks/fills por texto fallan). `playwright-cli` sí resuelve ambos. Dos fallos recurrentes que cubre: (1) el navegador crashea al abrir con `Target crashed` / `sandbox initialization failed: Operation not permitted`, y (2) el shadow DOM no es navegable desde el MCP del panel.

## Steps
1. Verificar instalación: `which playwright-cli && playwright-cli --version`. Si no está, pedir al usuario instalarlo (un clic en Settings -> Browser del dashboard). El `browser` MCP tool del panel NO es alternativa: no guarda PNG/webm a disco y su snapshot no entra al shadow DOM.
2. Ver output dir y verbos disponibles: `echo "$PLAYWRIGHT_MCP_OUTPUT_DIR"`, `playwright-cli --help`, `playwright-cli open --help`. Confirmar verbos de video: `video-start`, `video-stop`, `video-chapter`, `video-show-actions`.
3. Preparar entorno macOS (socket path): `mkdir -p /tmp/pws && export PWTEST_SOCKETS_DIR=/tmp/pws`. El socket path por defecto es demasiado largo y el `open` falla sin esto.
4. Crear `cli.config.json` con `{"launchOptions":{"args":["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}}`. El `--no-sandbox` es la clave: sin él Chrome crashea 'sandbox initialization failed: Operation not permitted' en el gateway confinado (loop de crash).
5. Abrir HEADLESS (sin `--headed`): `mkdir -p "$PLAYWRIGHT_MCP_OUTPUT_DIR"; cd "$PLAYWRIGHT_MCP_OUTPUT_DIR"; playwright-cli -s=<slug> open "<url>" --browser chrome --config "$PLAYWRIGHT_MCP_OUTPUT_DIR/cli.config.json"`. HEADED crashea 'Target crashed' por falta de display/GPU real. El canal `msedge` crashea igual (mismo tema de entorno, aunque Edge sea Chromium); usar `--browser chrome` (bundled estable, mismo motor Chromium). `open` SÍ acepta `--config`; `snapshot/console/screenshot` NO. Verificar con `snapshot` que cargó (ahora sí muestra refs reales).
6. Iniciar grabación: `video-start "recorrido.webm"` + `video-show-actions` + `video-chapter "N. paso"` antes de cada bloque lógico. El video graba el estado de la PÁGINA, no los comandos del agente, así que los re-snapshots no aparecen como pausa.
7. Para cada interacción: `snapshot` para obtener los refs `f#` reales (playwright-cli SÍ penetra el shadow DOM de web components), luego `fill <ref> <valor>` / `click <ref>`. Preferir el ref `f#` (identificado por su label cercano) sobre el match por texto/placeholder/role — ese match es frágil y en shadow DOM directamente falla.
8. **Re-snapshot tras cada expand/navegación**: los refs `f#` CAMBIAN al re-renderizar el menú. No reusar ni encadenar un ref viejo tras expandir un submenú; tomar snapshot fresco tras cada expansión.
9. `screenshot` guarda PNG a disco en `$PLAYWRIGHT_MCP_OUTPUT_DIR` (crearlo con `mkdir -p` antes). Capturar los pasos clave. `eval` suele requerir aprobación — evitarlo, preferir `snapshot`.
10. Al terminar: `video-stop`, `sleep 2`, `ls -lht *.webm *.png`, `close` (o `close-all`).
11. Entregar el `.webm` con `file_send` (acepta video/imagen/PDF, NO .zip).

## Gotchas
- `Target crashed` + `sandbox initialization failed: Operation not permitted` = falta `--no-sandbox`, NO es bug del sitio ni de la URL.
- `--headed` en gateway sin display = crash; usar headless siempre (graba video igual).
- Grabar ventana visible + verla en vivo es trabajo de la sesión PRINCIPAL, no de un subagente: el subagente corre headless/confinado, comparte el proceso de Playwright del padre y no muestra pantalla al usuario. NO delegar esto a un subagente.
- `eval()` requiere aprobación (suele estar bloqueado); no depender de él para leer `location.href` — usar `snapshot` que incluye 'Page URL'.
- Navegación de menú multinivel (3 niveles de submenú): el contenedor clickeable suele ser el `generic [cursor=pointer]` padre del texto, no el nodo de texto. Verificar con `find <texto>` que el submenú realmente se expandió antes de buscar el siguiente nivel; un doble-click colapsa lo que ya estaba abierto.
- Si el usuario pide un video 'más ágil', el ritmo del VIDEO no depende de tus pausas entre comandos (el video graba el estado de la página, no tus llamadas); reducir los `sleep` a 1-2s ayuda poco al resultado visual — no re-snapshotear de más es lo que lo acorta.
- El `browser` MCP del panel: útil solo para conducir en vivo que el usuario mira, pero inútil para evidencia publicable y para shadow DOM.
- Tras 2 intentos del mismo camino que crashea, cambiar de enfoque (headless, otro browser) en vez de insistir.
- Si el usuario pega credenciales en el chat, advertir que quedaron en el transcript y recomendar rotarlas; no repetir la contraseña en texto después.

## Equivalentes en Windows (PowerShell)
- Paso 3 (socket path): en macOS se usa `/tmp/pws`. En Windows crea una ruta corta propia, por ejemplo `New-Item -ItemType Directory -Force C:\pws | Out-Null; $env:PWTEST_SOCKETS_DIR = "C:\pws"`. Si `open` falla por la longitud del socket, es el mismo problema.
- Variable de salida: `$env:PLAYWRIGHT_MCP_OUTPUT_DIR` en lugar de `$PLAYWRIGHT_MCP_OUTPUT_DIR`; `New-Item -ItemType Directory -Force` en lugar de `mkdir -p`; `Start-Sleep -Seconds 2` en lugar de `sleep 2`; `Get-ChildItem *.webm, *.png` en lugar de `ls -lht`.
- El script `scripts/make_playwright_cli_config.py` es portable (solo escribe un JSON). Córrelo con `python` en Windows.
- Los argumentos `--no-sandbox`, `--disable-gpu` y `--disable-dev-shm-usage` y el modo headless se mantienen; no se verificó si en Windows son necesarios. Prueba sin ellos primero y agrégalos solo si Chrome crashea con `Target crashed`.
