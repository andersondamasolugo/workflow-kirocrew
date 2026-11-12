---
name: auto/jira-bulk-fetch-via-rest-fallback
description: Consultar campos de varias HU Jira Cloud via REST API con basic auth cuando las tools MCP fallan por scope
triggers: jira issue fetch, 401 scope does not match, agent-interface scope, jira rest api curl, atlassian basic auth, consultar HU jira, estimacion story points
source: auto
session_key: dashboard:chat-12-1792696717
created_at: 2026-10-22T20:54:07+00:00
---

## When to use
Cuando necesitas leer campos (summary, status, priority, estimacion, descripcion) de una o varias issues de Jira Cloud y las tools MCP de Atlassian de la sesion fallan con `401 Unauthorized; scope does not match` (token OAuth con scopes `*:jira:agent-interface` en vez del clasico `read:jira-work`).

## Steps
1. Intenta primero la tool MCP nativa (`getJiraIssue`) una vez en vivo — el comportamiento puede variar entre sesiones; no asumas por leccion vieja que falla.
2. Si devuelve `401 scope does not match`, el OAuth tiene el scope equivocado y no se puede sortear reescribiendo la llamada. Cae al fallback REST.
3. Consigue credenciales: las env vars que el usuario exporta en SU terminal NO llegan al entorno del agente (verifica con `env | grep -iE '^(JIRA|ATLASSIAN)'` — dara vacio). El token debe venir pegado en el chat o guardado en el vault/mcp.json que lee el gateway.
4. Si el usuario pega el token en texto plano: advertirle de inmediato que quedo expuesto en el transcript, redactarlo en todas las respuestas (`ATATT...<REDACTADO>`), usarlo solo para la tarea, y recomendar revocarlo/regenerarlo al terminar.
5. Valida la auth antes de iterar: `GET /rest/api/3/myself` con `-u email:token` debe dar HTTP 200.
6. Trae cada issue por su endpoint por-issue (fiable): `GET /rest/api/3/issue/<KEY>?fields=summary,status,issuetype,priority,timeoriginalestimate,customfield_10016,description`. NO uses `/search/jql` (puede dar 200 con lista vacia por el formato nuevo de la API).
7. La descripcion viene en ADF (Atlassian Document Format, JSON anidado): extrae texto plano recorriendo los nodos `type=text`.

## Gotchas
- `customfield_10016` es Story Points; suele venir vacio (la estimacion puede vivir en una tabla dentro de la descripcion).
- El API token (prefijo `ATATT...`) se genera en id.atlassian.com -> Security -> API tokens y puede caducar/revocarse entre turnos (401 'no existe o no tienes permiso') -> pedir uno nuevo.
- No eches el token en respuestas ni lo asumas inofensivo porque el usuario lo compartio voluntariamente.
- Solucion de raiz (accion del usuario en el dashboard): reconectar la integracion Atlassian pidiendo scopes clasicos `read:jira-work`, o guardar el token en el vault cifrado de Kiro Crew.
