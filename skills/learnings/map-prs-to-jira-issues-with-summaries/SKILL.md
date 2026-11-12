---
name: auto/map-prs-to-jira-issues-with-summaries
description: Mapea una lista de PRs de GitHub a sus issues de Jira y obtiene los summaries reales via API REST
triggers: mapear PR a Jira, extraer codigo HU de titulo de PR, Jira issue summary, lista PRs con links Jira, gh pr view HU, Jira REST search/jql
source: auto
session_key: dashboard:chat-6-1792509538
created_at: 2026-10-20T16:40:16+00:00
---

## When to use
Cuando el usuario tiene una lista de titulos/PRs de GitHub y quiere mapearlos a sus issues de Jira (codigo + nombre real), tipicamente en formato `[nombre](url)` o tabla markdown.

## Steps
1. Confirmar el owner/repo real con `git -C <dir> remote get-url origin` o `gh repo view`, no adivinar. Obtener la base de Jira del cliente (ej. `https://<site>.atlassian.net/browse/`).
2. Extraer el codigo de issue de cada titulo con regex tolerante a formato: `[A-Za-z]{2,4}[ _-]?\d{2,4}[ _-]?\d{2,5}` (cubre 'GD929 1465', 'Gd929-2239', 'feat(929-2239)', 'gd198 3719'). Normalizar a MAYUS-GUION (GD929-1465). OJO: pueden convivir varios proyectos Jira (GD929 vs GD198) en el mismo repo; no asumir un solo prefijo.
3. Para los PRs SIN codigo en el titulo, leer rama + body con `gh pr view <n> --repo <owner/repo> --json title,headRefName,baseRefName,body` y correr el mismo regex sobre `body + headRefName + title`. La rama (`feat/GD198-3719`) suele traer el codigo cuando el titulo no.
4. Un PR tipo Revert hereda la HU del PR que revierte; un PR con varios numeros en el titulo ('2908 2909 2910 2488') mapea a varias HUs.
5. Para los NOMBRES reales de las HU: las tools MCP de Atlassian suelen fallar con 401 'scope does not match' (token agent-interface). La via fiable es la API REST con basic auth email:apitoken.
   - Validar primero: `curl -s -o /dev/null -w 'HTTP %{http_code}' -u "$EMAIL:$TOKEN" https://<site>.atlassian.net/rest/api/3/myself` (espera 200).
   - Traer todos en una consulta: GET `/rest/api/3/search/jql` con `--data-urlencode 'jql=key in (K1,K2,...)'`, `fields=summary`, `maxResults=50`. Parsear `issues[].key` + `fields.summary` con python3.
6. Entregar en el formato pedido por el usuario (lista `[nombre](url)` o tabla).

## Gotchas
- Las env vars que el usuario exporta en SU terminal NO llegan al entorno del agente (corre en otro host). El agente debe recibir el token en el comando.
- Si el usuario pega un API token/credencial en texto plano en el chat: advertir que quedo expuesto en el transcript, redactarlo en todas las respuestas, y recomendar revocarlo/regenerarlo en id.atlassian.com -> Security -> API tokens. Nunca repetir el valor.
- El endpoint REST de Jira da 404 sin autenticacion (no 401), lo que puede confundir: Jira Cloud exige login para leer summary.
- Regex demasiado estricto a 'GD929-####' pierde variantes con espacio, minuscula o prefijo distinto; usar el patron tolerante y normalizar despues.
