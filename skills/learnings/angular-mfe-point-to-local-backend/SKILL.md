---
name: auto/angular-mfe-point-to-local-backend
description: Diagnose and configure an Angular micro-frontend workspace to point at local microservices instead of a cloud/AWS gateway
triggers: angular proxy.conf.json, urlService local, custom-webpack proxyConfig, microfront local backend, pathRewrite context-path, apuntar front a ms local, apuntar frontend a local, urlService, proxy.conf.json, micro-frontend local backend, 401 redirect SSO local
source: auto
session_key: dashboard:ui
created_at: 2026-10-29T20:08:38+00:00
version: 2
---

## When to use
When an Angular micro-frontend app (shell + remotes) that normally talks to a single cloud API gateway must be pointed at several locally-running microservices on distinct ports/context-paths. Typical symptoms: 404 at `localhost:4200`, redirect loops to Cognito/SSO, or 401s bubbling into a SAML/SSO redirect.

## Steps
1. **Find how the base URL is injected.** Locate the env mechanism (e.g. a `.env` consumed by an `inject-env` script that bakes values into a `process-env-polyfill.ts`). The var that controls the backend (often `urlService`) is the ONLY thing that decides where calls go, NOT the launch command. Confirm whether the app reads the file directly or needs a re-inject step after editing.
2. **Understand URL composition.** Read the service that builds request URLs (e.g. `set-route-api.service.ts`). A single base + path-segment concatenation (`${urlService}segment/api/v1`) only works against a gateway host; local MSs on different ports/context-paths cannot be covered by one absolute URL. This forces a dev-server proxy.
3. **Set the base URL relative** (`urlService=/`) and create `proxy.conf.json` mapping each path segment to its local port, using `pathRewrite` when the local context-path prefix differs (e.g. `/autorizacion-salud` → `localhost:8080/gb-autorizacion-salud`). Comment (don't delete) the original cloud block so it's reversible.
4. **Check the serve builder before using `--proxy-config`.** If `angular.json` serve uses a custom builder (e.g. `@angular-builders/custom-webpack:dev-server`), the CLI flag is ignored — calls stay on `:4200` (404, `Remote address :4200`). Declare `proxyConfig` inside each project's `serve.options` in `angular.json` instead. Edit `angular.json` with a Node script (not a text tool) to avoid breaking the large JSON, and back it up first.
5. **Identify the micro-front that makes HTTP calls.** In a shell+remotes setup the shell (where the shared lib lives) issues the calls, so its port's proxy is what matters. Remotes loaded from external CDNs (not running locally) will always hit cloud auth — those cannot be run locally.
6. **Trace auth redirects to their true source.** A redirect to a corporate SSO/SAML host is usually NOT backend-origin: grep the MS source (excluding build/ dirs) for `saml`/`sso` — if empty, the front's HTTP error interceptor is redirecting on 401. Fix at the interceptor (skip redirect when env is local) and/or relax backend JWT.
7. **Relax backend auth for local.** Look for a conditional security config (`@ConditionalOnProperty("app.security.jwt.enabled")` + a `LocalSecurityConfig`/`NoOpSecurityConfig`). Set the flag false via env var (relaxed binding: `APP_SECURITY_JWT_ENABLED=false`). Verify EACH service honors it — non-conditional `SecurityConfig` classes ignore the flag and keep returning 401, including internal facade→fragment forwards that propagate the (dummy) Authorization header.
8. **Validate after each edit.** `node -e "JSON.parse(...)"` for JSON files, grep the generated polyfill to confirm the re-inject ran, `lsof -iTCP:<port> -sTCP:LISTEN` to confirm a service is up, and read facade logs to see which downstream service actually returned the 401.
9. **Track and protect local-only edits.** Keep an inventory file (e.g. `CONFIG-LOCAL.md`) listing every local-only change and how to revert. Add new untracked artifacts to `.gitignore`; already-tracked files cannot be ignored without `git rm --cached`, so flag them explicitly as 'do not commit'. When reverting, `git restore` ONLY your own patches and preserve unrelated work-in-progress from other branches/features.

## Gotchas
- Editing the `.env` is useless until the inject/bake step re-runs; the app uses the polyfill, not the `.env`.
- `--proxy-config` on the CLI silently does nothing with custom-webpack builders — `Remote address :4200` on the 404 is the tell.
- A relative `urlService=/` cannot route an absolute token/login endpoint (Cognito, portal) — those stay direct to cloud and may still 403/401; check whether they're wrapped in `catchError`.
- `APP_SECURITY_JWT_ENABLED=false` only affects services whose security config is conditional; fragment services behind a facade often aren't and keep 401ing on the forwarded dummy token.
- A one-use OAuth `code` consumed twice (double `getTokensAndMenu` dispatch) causes a login→redirect loop with `invalid_grant`.
- `.env` and local scripts may be git-ignored (good) while code patches are tracked (risky) — separate them clearly before any commit.
- Don't delete original cloud config; comment it so switching back is one edit + re-inject.
