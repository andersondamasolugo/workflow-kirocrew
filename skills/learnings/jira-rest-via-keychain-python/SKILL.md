---
name: auto/jira-rest-via-keychain-python
description: Read Jira issues/epics via REST API using a Keychain-stored token, bypassing the MCP connector
triggers: jira rest, keychain token, atlassian api, read epic, jira issue python, bypass mcp atlassian, flatten adf description
source: auto
session_key: dashboard:chat-29-1793811970
created_at: 2026-11-04T18:12:45+00:00
---

## When to use
When you need to read Jira issues, epics, or run JQL searches on a Mac where the Atlassian MCP connector is unavailable or requires an interactive auth banner. Pull the API token from the macOS Keychain and call the Jira Cloud REST API directly with python3.

## Steps
1. Retrieve the token from Keychain: `security find-generic-password -s <service-name> -w` (service name is where the Jira API token is stored).
2. Build a Basic auth header: `base64(email:token)`.
3. Base URL is `https://<site>.atlassian.net/rest/api/3/`.
4. Validate auth first with `GET myself` — a 200 and a display name confirm the token works before doing real work.
5. Fetch an issue with field projection: `issue/<KEY>?fields=summary,status,description,issuelinks`.
6. For children of an epic, run JQL: `search/jql?jql=<url-encoded: parent=<EPIC-KEY> ORDER BY key>&fields=summary,status,issuetype&maxResults=50`.
7. Descriptions come back as ADF (Atlassian Document Format) JSON — flatten recursively: concatenate `text` nodes and append a newline after `paragraph`/`listItem`/`heading` node types.
8. Write the script to a scratch dir and run it; keep field lists narrow to limit payload.

## Gotchas
- Never hardcode the token; always read it from Keychain at runtime.
- The description field is ADF, not plain text or HTML — a naive `str()` gives nested JSON. Flatten it.
- `search/jql` is the current endpoint; project only the fields you need via `&fields=`.
- Validate with `myself` before batch reads so an auth failure surfaces immediately instead of mid-loop.
- URL-encode the entire JQL string.
- Email and site are environment-specific — parameterize them, don't assume.

## Multiplataforma (macOS / Windows / Linux)
El procedimiento no depende de macOS: solo cambia dónde vive el token.

| Sistema | Dónde guardar el token | Cómo se lee |
|---------|------------------------|-------------|
| macOS | Llavero (`jira-api-token`) | `security find-generic-password -s jira-api-token -w` |
| Windows | Variable de entorno de usuario `JIRA_API_TOKEN` | `os.environ` / `$env:JIRA_API_TOKEN` |
| Linux | Secret Service (`secret-tool`) o `JIRA_API_TOKEN` | `secret-tool lookup service jira-api-token` |

El kit trae los dos pasos ya resueltos y portables:
- `dev-flows/scripts/read_secret.py <servicio> <VARIABLE>`: busca primero la variable de entorno y luego el almacén del sistema.
- `dev-flows/scripts/jira_read.py GD929-1234` (o `--jql "..."`): valida `myself`, trae el issue y aplana el ADF. Requiere `JIRA_SITE` (por ejemplo `miempresa.atlassian.net`) y `JIRA_EMAIL`. Usa solo la librería estándar de Python.

En Windows, usa `python` en lugar de `python3` y define las variables con `[Environment]::SetEnvironmentVariable("JIRA_API_TOKEN", <valor>, "User")` desde tu propia terminal (nunca en el chat); reinicia Kiro Crew para que la herede.
