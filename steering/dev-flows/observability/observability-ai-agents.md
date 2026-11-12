---
inclusion: auto
name: observability-ai-agents
description: AI agent observability guide when working with AI agents, Vertex AI, Gemini, LLM Observability, Cloud Run Dockerfile with datadog-init, or DD_LLMOBS environment variables.
---

# AI Agent Observability — Cloud Run + Datadog (Seguros Bolívar)

## Mandatory Process

Before any configuration, file a Jira request to create the service in Datadog, obtain the API Key, and use the corporate standard Docker image.

## In-Container Instrumentation (Cloud Run)

Cloud Run Gen1 runs the Datadog agent inside the same container using `datadog-init` as entrypoint and `ddtrace-run` for automatic instrumentation.

```dockerfile
# ✅ Good — Dockerfile with datadog-init for Cloud Run
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

COPY --from=gcr.io/datadoghq/serverless-init:latest /datadog-init /app/datadog-init

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

ENV DD_SERVICE=my-ai-agent
ENV DD_ENV=prod
ENV DD_VERSION=1.0.0
ENV DD_SITE=datadoghq.com
ENV DD_TRACE_ENABLED=true
ENV DD_APM_ENABLED=true

ENTRYPOINT ["/app/datadog-init"]
CMD ["ddtrace-run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# ❌ Bad — no datadog-init or ddtrace-run
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Include `ddtrace` in `requirements.txt`.

## Environment Variables for Cloud Run

The API Key MUST be stored in Google Cloud Secret Manager and referenced via `secretKeyRef`. Never hardcode.

```yaml
# ✅ Good — observability variables in cloudrun-prod.yaml
env:
  - name: DD_SERVICE
    value: "my-ai-agent"
  - name: DD_ENV
    value: "prod"
  - name: DD_VERSION
    value: "1.0.0"
  - name: DD_SITE
    value: "datadoghq.com"
  - name: DD_TRACE_ENABLED
    value: "true"
  - name: DD_APM_ENABLED
    value: "true"
  - name: DD_LLMOBS_ENABLED
    value: "true"
  - name: DD_LLMOBS_ML_APP
    value: "my-ai-agent-app"
  - name: DD_LOGS_ENABLED
    value: "false"
  - name: DD_SERVERLESS_LOG_LEVEL
    value: "OFF"
  - name: DD_API_KEY
    valueFrom:
      secretKeyRef:
        name: datadog-api-key
        key: latest

# ❌ Bad — exposed API Key
# - name: DD_API_KEY
#   value: "abc123secret"
```

## Enable LLM Observability in Code

Enable LLM Observability to capture prompts, responses, execution times, and model behavior.

```python
# ✅ Good — enable LLM Observability with ddtrace
from ddtrace.llmobs import LLMObs
import os

LLMObs.enable(
    ml_app=os.getenv("DD_LLMOBS_ML_APP", "my-ai-agent-app"),
    site=os.getenv("DD_SITE", "datadoghq.com"),
    agentless_enabled=True,
)

# ❌ Bad — no LLM Observability, model interactions invisible
```

## AI Observability Security

Never send PII or secrets in prompts. Redact automatically before sending. Validate outputs before executing side effects.

```python
# ✅ Good — PII redaction before prompt
sanitized_input = redact_pii(user_input)
response = await model.generate(prompt=sanitized_input)
validated = validate_model_output(response)

# ❌ Bad — raw PII to model, unvalidated output
response = await model.generate(prompt=user_input)
await execute_action(response.text)
```

## Post-Deployment Validation

Verify in Datadog after deploying:

- [ ] APM traces appear for the service
- [ ] LLM interactions are recorded in LLM Observability
- [ ] No authentication errors with API Key
- [ ] Response times are consistent
- [ ] Token costs (input/output) are visible

## Prohibitions

- Never deploy AI agents without LLM Observability enabled (`DD_LLMOBS_ENABLED=true`).
- Never expose API Key in code or plain variables — use Secret Manager with `secretKeyRef`.
- Never deploy without a prior Jira request and corporate standard Docker image.
- Never send PII or secrets in prompts to the model — redaction is mandatory.
