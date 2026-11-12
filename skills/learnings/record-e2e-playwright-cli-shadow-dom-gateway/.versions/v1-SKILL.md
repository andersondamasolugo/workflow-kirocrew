---
name: auto/record-e2e-playwright-cli-shadow-dom-gateway
description: Grabar pruebas E2E con playwright-cli en un gateway headless contra apps con web components (shadow DOM), sorteando crashes de sandbox
triggers: playwright-cli, grabar video E2E, web components shadow DOM, sb-ui, Target crashed sandbox, navegacion menu micro-frontend, evidencia publicable pruebas
source: auto
session_key: dashboard:chat-3-1792441022
created_at: 2026-10-27T21:53:41+00:00
---

## When to use
Cuando el usuario pide grabar un recorrido E2E con video/screenshots publicables contra una app web (especialmente de micro-frontends con web components en shadow DOM) desde un gateway headless sin display real. El `browser` MCP del panel NO sirve aquí: renderiza en vivo pero NO persiste archivos a disco y su snapshot NO penetra el shadow DOM de componentes tipo `sb-ui-*` (no ves los refs del menú). `playwright-cli` sí resuelve ambos.

## Steps
1. Verificar instalación: `which playwright-cli && playwright-cli --version`. Si no está, pedir al usuario instalarlo (un clic en Settings -> Browser del dashboard).
2. Preparar entorno macOS: `mkdir -p /tmp/pws && export PWTEST_SOCKETS_DIR=/tmp/pws` (el socket path por defecto es demasiado largo y falla).
3. Crear `cli.config.json` con `{"launchOptions":{"args":["--no-sandbox","--disable-gpu","--disable-dev-shm-usage"]}}` — sin `--no-sandbox` Chrome crashea 'sandbox initialization failed: Operation not permitted' en el gateway confinado.
4. Abrir HEADLESS (sin `--headed`): `playwright-cli -s=<slug> open "<url>" --browser chrome --config <ruta>/cli.config.json`. HEADED crashea 'Target crashed' por falta de display/GPU. El canal `msedge` crashea igual; usar `--browser chrome` (mismo motor Chromium). `open` SÍ acepta `--config`; `snapshot/console/screenshot` NO.
5. Iniciar grabación: `video-start "recorrido.webm"` + `video-show-actions` + `video-chapter "N. paso"` antes de cada bloque. El video graba el estado de la PÁGINA, no los comandos del agente, así que los re-snapshots no aparecen como pausa.
6. Para cada interacción: `snapshot` para obtener los refs `f#` reales (playwright-cli SÍ penetra el shadow DOM de web components), luego `fill <ref> <valor>` / `click <ref>`. Preferir el ref `f#` sobre el match por texto/placeholder/role (ese match es frágil).
7. **Re-snapshot tras cada expand/navegación**: los refs `f#` cambian al re-renderizar el menú. No reusar un ref viejo tras expandir un submenú.
8. `screenshot` guarda PNG a disco en `$PLAYWRIGHT_MCP_OUTPUT_DIR` (crearlo con `mkdir -p` antes). Capturar los pasos clave.
9. Al terminar: `video-stop`, `sleep 2`, `close`. Listar artefactos: `ls -lht *.webm *.png`.
10. Entregar el `.webm` con `file_send` (acepta video/imagen/PDF, NO .zip).

## Gotchas
- Grabar ventana visible + verla en vivo es trabajo de la sesión PRINCIPAL, no de un subagente: el subagente corre headless/confinado, comparte el proceso de Playwright del padre y no muestra pantalla al usuario.
- `eval()` requiere aprobación (suele estar bloqueado); no depender de él para leer `location.href` — usar `snapshot` que incluye 'Page URL'.
- Navegación de menú multinivel (3 niveles de submenú): el contenedor clickeable suele ser el `generic [cursor=pointer]` padre del texto, no el nodo de texto. Verificar con `find <texto>` que el submenú realmente se expandió antes de buscar el siguiente nivel; un doble-click colapsa lo que ya estaba abierto.
- Tras 2 intentos del mismo camino que crashea, cambiar de enfoque (headless, otro browser) en vez de insistir.
- Si el usuario pega credenciales en el chat, advertir que quedaron en el transcript y recomendar rotarlas; no repetir la contraseña en texto después.
