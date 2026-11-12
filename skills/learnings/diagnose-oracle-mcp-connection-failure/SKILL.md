---
name: auto/diagnose-oracle-mcp-connection-failure
description: Diagnose why an Oracle MCP server fails to connect despite configured credentials, distinguishing env propagation, config source, and driver mode causes
triggers: oracle MCP connection failure, faltan variables de entorno, DPY-3015, password verifier not supported, thin mode thick mode, instant client missing, mcp.json credentials not loaded
source: auto
session_key: dashboard:chat-26-1793732446
created_at: 2026-11-04T00:39:20+00:00
---

## When to use
An MCP server (Oracle via python-oracledb, but the method generalizes) returns a connection/credential error even though credentials appear correctly set in config. The surface error is often misleading (e.g. 'missing env vars' when the real cause is elsewhere). Use this to find root cause with hard evidence instead of repeatedly retrying the ping or re-registering credentials.

## Steps
1. Reproduce the failing call once and capture the exact error string. Do not retry it repeatedly — an environment/credential error is not fixed by retrying.
2. Confirm the config file content WITHOUT exposing secrets: read the config and print values with passwords masked. Verify the credential keys exist and are non-empty.
3. Check for MULTIPLE config files. A common trap: the file the user edited (e.g. `~/.kiro/crew/mcp.json`) is not the one the runtime actually loads (e.g. `~/.kiro/settings/mcp.json`). Grep for the server name across candidate config locations and compare which one has the entry.
4. Test credential propagation directly: run the server's launcher or driver with the env explicitly passed, and assert each required var resolved (expect something like `MISSING: []`). If it connects/authenticates here but the live process fails, the cause is env propagation, not the credentials.
5. If authentication itself fails with a driver-specific code, read the exact code. For python-oracledb, `DPY-3015: password verifier 0x939 not supported in thin mode` means the DB uses an old (10g) verifier that only THICK mode supports.
6. For thick-mode requirements, read the server source to find where it calls `init_oracle_client(lib_dir=...)` and under what condition (often `if os.path.isdir(_IC_DIR)`). Then check whether that Instant Client directory and `libclntsh` actually exist. A missing Instant Client silently falls back to thin mode.
7. Separate symptom from root cause in the report: the 'missing env' message can be a stale-process artifact while the real wall is a missing native library. State each check and its hard result in a table.

## Gotchas
- A process with `command`-launched MCP reads its `env` only once at startup; credentials added after launch require a gateway/process restart to take effect.
- Restarting the product's own gateway from inside the agent is typically blocked by a self-protection policy (`self-protection-restart`). Do not re-spell the command to evade it — ask the user to run it from an external terminal or dashboard.
- The 'missing variables' error and the real driver error can coexist: fix propagation AND the native dependency, or the connection still fails.
- Avoid shell patterns that get blocked as unsafe (redirects, `2>&1`, command substitution, backgrounding) when the runtime restricts them; prefer plain read-only commands or file-reading tools.
- Always have a parallel path that does not depend on the blocked resource (e.g. read the DDL/JPA model from the source repos instead of querying the live DB).
