---
name: auto/angular-mf-microfront-rename-migration
description: Rename/consolidate an Angular Module Federation microfront while keeping remote wiring synchronized and git history preserved
triggers: microfront rename, module federation migration, remote wiring, consolidate MFE, angular monorepo refactor, remoteEntry wiring, feature lazy route
source: auto
session_key: dashboard:chat-19-1793122883
created_at: 2026-10-28T14:23:18+00:00
---

## When to use
When migrating or renaming an Angular Module Federation (webpack) microfront inside a monorepo — e.g. consolidating a per-screen remote into a domain MFE, or renaming a remote. The shell loads remotes dynamically and the wiring is spread across several files that must stay in sync or the remote won't load.

## Steps
1. **Map the wiring before touching anything.** Read every file that references the old MFE: `angular.json` (project block), `package.json` (start/build/test scripts), shell `constants.ts` (MICRO_FRONTS entry + union type), shell `config-routes.ts` (REMOTE_NAME_MAP), shell `app-routing.module.ts` (the public shell path), the remote's `webpack.config.js` / `webpack.prod.config.js`, and `remote-entry.routing.ts`.
2. **Distinguish three categories of references** before editing: (a) wiring that must change (project name, uniqueName, remoteName, S3 path, port, scripts, shell maps); (b) legitimate strings that stay (the BE endpoint basePath, S3 LOAD_PATH, CSV names, the public shell URL kept stable to not break menu/permissions); (c) local-only files that never get committed (menu mocks, `historyApiFallback` in webpack).
3. **Decide the shell entry model.** Prefer one shell entry per domain path (e.g. `/arl`) with sub-screens as internal lazy routes in `remote-entry.routing.ts`, so adding future screens never touches the shell. Changing the public shell path also changes the AuthGuard-validated URL — flag that the real FCA/menu transaction must be updated externally; only the local mock is in-repo.
4. **Create the new project / move code into `features/<screen>/{containers,components,shared}`.** Keep NgModule + webpack ModuleFederationPlugin — do NOT switch to standalone bootstrap (`app.config.ts`/`app.routes.ts`) or `federation.config.js`; that breaks this repo's federation.
5. **Delete the old project last**, then grep the whole repo for the old name/remoteName to confirm zero residual wiring (only category-b strings should remain).
6. **Verify with three builds before committing:** `ng build <new-mfe>` (confirm remoteEntry emitted + lazy chunk resolves), `ng build shell`, and `jest <new-mfe>`. All must be EXIT 0 / green.
7. **Stage selectively by path**, excluding local-only files. Confirm git detects moved files as renames (preserves history) rather than delete+add.
8. **Commit via `git commit -F <scratch-file>`** (not `-m` with parens/slashes — they break the shell), then `git push origin <branch>` as a single isolated command with the branch named explicitly.

## Gotchas
- The shell loads remotes dynamically (`loadRemoteModule` + REMOTE_NAME_MAP), so the shell's `webpack.config.js` does NOT need a static `remotes` entry for a new MFE — the only change there (`historyApiFallback`) is local-only.
- Keeping the public shell URL stable avoids breaking menu/permissions; if you must change it, the AuthGuard compares the exact URL against the FCA transaction, so coordinate the external menu change or the route rebounds to home.
- Commit messages with `(TICKET-123)` or slashes break `printf`/`-m`; always write the message to a scratch file and use `-F`.
- Local-only files to always exclude: menu mock (`fca.mock.ts`), `menu-permissions.service.ts`, and the shell `webpack.config.js` `historyApiFallback` tweak.
- `.kiro/` is typically gitignored — don't force-commit docs there; put repo-facing docs in a versioned path (e.g. the MFE's `README.md`) and leave the `.kiro` steering copy local.
- Don't apply hexagonal architecture to a presentation-layer MFE; the repo pattern is containers/components + services + interfaces.
