---
inclusion: auto
name: observability-apm-tracing
description: APM, distributed tracing, golden signals, custom metrics, and tagging guide when working with Datadog instrumentation, metrics, or DogStatsD.
---

# APM, Tracing & Metrics — Datadog (Seguros Bolívar)

## Distributed Tracing (APM)

Instrument all services with Datadog APM following the OpenTelemetry standard. Propagate `trace.id` and `span.id` across all internal and external calls.

```python
# ✅ Good — ddtrace instrumentation in FastAPI
# ddtrace-run uvicorn app.main:app
from ddtrace import tracer, patch_all

patch_all()  # auto-instruments httpx, sqlalchemy, redis, etc.

@tracer.wrap(service="policy-service", resource="create_policy")
async def create_policy(data: PolicyRequest) -> PolicyResponse:
    policy = await policy_repo.save(data)
    return PolicyResponse.from_orm(policy)

# ❌ Bad — no instrumentation, disconnected traces
async def create_policy(data: PolicyRequest) -> PolicyResponse:
    return await policy_repo.save(data)
```

```java
// ✅ Good — Spring Boot with dd-java-agent (automatic instrumentation)
// java -javaagent:/path/to/dd-java-agent.jar -Ddd.service=policy-service -Ddd.env=production app.jar

// ❌ Bad — no agent, no traces
```

## Golden Signals — Required Metrics

Every service must expose the Four Golden Signals:

| Signal | Description | Example |
|--------|-------------|---------|
| Latency | Request response time | p50, p95, p99 of request duration |
| Traffic | Demand on the service | Requests per second |
| Errors | Failed request rate | % of 5xx responses |
| Saturation | Resource utilization | CPU, memory, connection pool |

## Metric Naming Convention

Structure: `prefix_metric_unitstype`. Counters end in `_total`. Include base unit as suffix (`_seconds`, `_bytes`).

```
# ✅ Good
api_http_requests_total
http_request_duration_seconds
database_connection_pool_usage_ratio
system_memory_usage_bytes

# ❌ Bad — generic names without convention
requests
duration
memory
```

## Custom Metrics with DogStatsD

Required tags on every metric: `service`, `env`, `team`. Add `platform`, `channel`, and business context as applicable.

```python
# ✅ Good — business custom metric with complete tags
from datadog import statsd

statsd.increment("policy_service.policies.created_total", tags=[
    "env:production",
    "service:policy-service",
    "team:policies",
    "platform:ciencuadras",
    "channel:web",
    "coverage:premium",
])

statsd.histogram("policy_service.quote.response_time_seconds", elapsed_s, tags=[
    "env:production",
    "service:policy-service",
    "endpoint:/api/v1/quotes",
])

# ❌ Bad — metric without tags, generic name
statsd.increment("created")
```

## Required Tagging

All telemetry MUST include corporate tags: `env`, `service`, `version`, `team`, `region`, `platform`, `criticidad`, `scope`.

```yaml
# ✅ Good — complete tags in Kubernetes deployment
metadata:
  labels:
    tags.datadoghq.com/env: production
    tags.datadoghq.com/service: policy-service
    tags.datadoghq.com/version: "1.2.0"
spec:
  template:
    metadata:
      labels:
        tags.datadoghq.com/env: production
        tags.datadoghq.com/service: policy-service
        tags.datadoghq.com/version: "1.2.0"
        team: team-phoenix
        platform: ciencuadras
        region: us-east-1

# ❌ Bad — no tags, Datadog cannot correlate
```

## Health Checks

Expose `/health` and `/ready` endpoints on every service. Integrate with Datadog Synthetics or HTTP checks.

```python
# ✅ Good — health check with dependency verification
@app.get("/health")
async def health():
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    return {
        "status": "healthy" if (db_ok and redis_ok) else "degraded",
        "checks": {"database": db_ok, "redis": redis_ok},
    }

# ❌ Bad — health check that always returns ok
@app.get("/health")
async def health():
    return {"status": "ok"}
```

## Prohibitions

- Never deploy services without APM instrumentation (`ddtrace`, `dd-java-agent`, or `dd-trace-js`).
- Never create metrics without required tags (`env`, `service`, `version`, `team`).
- Never deviate from the Golden Path without Observability team approval.
