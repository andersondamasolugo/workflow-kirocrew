---
name: auto/diagnose-proxied-local-ms-403-auth-layers
description: Aislar un 403/401 del FE local hacia microservicios proxeados distinguiendo proxy vs filtro de seguridad del MS vs login del front
triggers: 403 local, proxy devuelve 403, X-Powered-By Express, JwtAuthenticationFilter, JWKS local0000, ms local auth, token sessionStorage, ng serve proxy
source: auto
session_key: dashboard:chat-21-1793280258
created_at: 2026-10-30T00:08:15+00:00
---

## When to use
Un FE Angular en local apunta a microservicios locales por proxy (ng serve + proxy.conf.json) y las llamadas de negocio devuelven 403/401, aun con los MS arriba (health 200). Sirve para separar las capas de auth y no parchear la equivocada.

## Steps
1. **Aísla las tres capas con curl, mismo endpoint:**
   - Directo al MS con el context-path real (ej. `/gb-<ctx>/api/v1/...`).
   - Directo SIN el prefijo que agrega el proxy (debe dar 404, confirma que el pathRewrite es necesario).
   - Por el proxy (`:4200/<ruta-sin-prefijo>`).
   Usa `curl -s -D - -o /dev/null <url> | grep -iE 'HTTP/|X-Powered-By|WWW-Authenticate|Location|Server'`.
2. **Interpreta los headers:**
   - Directo gb- 403 == por-proxy 403 (mismo status) y sin-prefijo 404 → el proxy reescribe bien y solo PROPAGA el 403; el muro está en el MS. (`X-Powered-By: Express` lo agrega el dev-server al reenviar; NO significa que Express generó el error.)
   - health del MS 200 pero el endpoint 403 → el MS tiene un filtro de seguridad que protege todo salvo `/actuator/health`.
3. **Confirma que es JWT:** repite con `-H '[REDACTED: credential]'`. Si pasa de 403 a 401 con un mensaje tipo `Invalid JWT serialization: Missing dot delimiter`, hay un `JwtAuthenticationFilter` activo que exige un JWT real.
4. **Verifica contra qué JWKS valida el MS** (en su log de arranque o config): si el `JWKS URI` apunta a un user-pool placeholder/inexistente (ej. `..._local0000`), el MS NO puede validar NINGÚN token en local, ni uno real — hasta apuntarlo al pool real.
5. **Separa las capas de auth antes de arreglar:** el bypass del login del FE (sembrar `document`/token mock en sessionStorage) resuelve SOLO la carga del menú del front. La auth JWT de CADA MS es una capa independiente que un token mock no satisface.
6. **Elige el fix por la capa real, no por síntoma:**
   - Para abrir el MS en local: ver si su `SecurityConfig` está bajo `@ConditionalOnProperty(app.security.jwt.enabled,...,matchIfMissing=true)` y si existe un `LocalSecurityConfig` gemelo con `havingValue=false` (permitAll). Si NO existe, poner el flag en false DESTRUYE la cadena de seguridad → Spring aplica su auto-config default (formLogin) → 'pide login' / 500. En ese caso hay que crear el LocalSecurityConfig o apuntar el JWKS al pool real.
   - Para probar con token real: apuntar el JWKS/pool al real de dev + sembrar un access_token fresco en sessionStorage, entrando SIN `?code=` en la URL.

## Gotchas
- No asumas que el 403 es del proxy por ver `X-Powered-By: Express`: el dev-server lo estampa aunque solo propague el status del MS. La prueba dura es que el MS directo da el mismo status.
- Poner `APP_SECURITY_JWT_ENABLED=false` solo funciona en MS que tienen un `LocalSecurityConfig` con `havingValue=false`; en los que no, lo ROMPE (500 / pide login). Verifica la existencia del archivo antes.
- Un bypass de token en el componente del front (sembrar sessionStorage) NO abre los MS: si es eso lo que necesitás, el fix es del lado backend. Revierte el bypass del front si el 403 venía del MS.
- Las env vars de los MS (pool id, flags) solo aplican al relanzar el proceso; si los MS ya estaban corriendo, el cambio no tuvo efecto.
