---
name: auto/angular-mfe-point-to-local-backend
description: Apunta un front Angular multi-MFE (que usa una sola baseUrl) a microservicios locales en puertos distintos via proxy.conf.json
triggers: angular proxy.conf.json, urlService local, custom-webpack proxyConfig, microfront local backend, pathRewrite context-path, apuntar front a ms local
source: auto
session_key: dashboard:ui
created_at: 2026-10-29T20:08:38+00:00
---

## When to use
Un frontend Angular multi-microfront (shell + remotes) arma UNA sola `baseUrl` (`${urlService}${segmento}/api/v1`) que en dev/prod resuelve contra un API Gateway unico, y quieres apuntarlo a microservicios corriendo en LOCAL donde cada MS vive en un puerto distinto con un context-path con prefijo (p.ej. `gb-`). Una sola `urlService` NO puede cubrir N backends en puertos distintos: la solucion estandar es un `proxy.conf.json` del dev-server que reparte por segmento.

## Steps
1. **Entiende como arma la URL el front.** Lee el servicio que compone las rutas (p.ej. `SetRouteApiService.setBaseUrl`) y las constantes de segmento (`APIURL_*`, `API_VERSION`). Confirma que es `urlService + <segmento> + /api/v1`.
2. **Mapea cada segmento a su puerto+context-path local.** Lista los MS locales con su puerto y context-path real (el health check 200 te lo confirma). El front llama `/autorizacion-salud/...` pero el MS escucha en `:8080/gb-autorizacion-salud/...` → el proxy debe cambiar SOLO el prefijo, el `/api/v1` ya va dentro del context-path.
3. **Pon `urlService=/` (relativa) en el `.env`**, comentando el bloque DEV (dejalo reversible). Si el front hornea el `.env` en un polyfill via un script (`npm run env:inject`), RE-INYECTA tras cada edicion — el front no lee el `.env` directo.
4. **Crea `proxy.conf.json`** en la raiz, una entrada por segmento: `{"/autorizacion-arl": {"target":"http://localhost:8087","pathRewrite":{"^/autorizacion-arl":"/gb-autorizacion-arl"},"secure":false,"changeOrigin":true,"logLevel":"debug"}}`.
5. **Declara el proxy en `angular.json`, NO por flag CLI.** Si el builder de serve es `@angular-builders/custom-webpack:dev-server`, IGNORA `--proxy-config` por linea de comando → la llamada se queda en `:4200` y da 404 (`Remote address [::1]:4200`). Pon `"proxyConfig": "proxy.conf.json"` dentro de `architect.serve.options` de cada proyecto (respalda `angular.json.bak`). Reinicia `ng serve` (solo se lee al arrancar).
6. **Verifica el proxeo:** la consola del `ng serve` muestra `[HPM] Proxy created: /autorizacion-salud -> http://localhost:8080`, y la llamada deja de ir a `:4200`.

## Gotchas
- **404 con `Remote address [::1]:4200`** = el proxy NO se aplico; casi siempre el builder custom-webpack ignorando el flag CLI → muevelo a `angular.json`.
- **El `.env` suele estar git-ignored** pero `proxy.conf.json`, `angular.json.bak` y cualquier doc de config NO lo estan: agregalos al `.gitignore`. Cuidado al hacer `echo >> .gitignore` si hay una regla `docs/` previa — puede concatenar mal el path; verifica con `git check-ignore <archivo>`.
- **`angular.json` es un archivo TRACKEADO**: editarlo para el proxy lo deja modificado en git. NO se puede ignorar sin `git rm --cached`. Hay que excluirlo manualmente al commitear (git restore antes del commit).
- **El proxeo NO resuelve auth.** Si los MS locales corren con Cognito/JWT dummy, las llamadas autenticadas daran 401/403; un interceptor del front puede traducir el 401 en un redirect a SSO/Cognito. El proxy solo enruta, no autentica.
- **Login/token NO va por el proxy**: el canje de token suele ir a un host absoluto de Cognito/API Gateway (no relativo), asi que `urlService=/` no lo toca; ese flujo puede fallar aparte (403/CORS, code de un solo uso).
- Edita `angular.json` (JSON grande) con un script node que parsee+reescriba, no a mano, para no romper el JSON.
