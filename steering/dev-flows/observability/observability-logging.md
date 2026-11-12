---
inclusion: auto
name: observability-logging
description: Structured logging and Datadog log correlation guide when working with logs, loggers, formatters, or logging configuration.
---

# Structured Logging — Datadog (Seguros Bolívar)

## JSON Required, Plain Text Forbidden

All logs MUST be structured JSON. Never use `print()`, `System.out.println()`, or `console.log()` in production. Send logs to Datadog via stdout/stderr or Datadog Agent, never to local files.

```python
# ✅ Good — structured JSON log
import logging
import json_log_formatter

formatter = json_log_formatter.JSONFormatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger("policy-service")
logger.addHandler(handler)

logger.info("policy_created", extra={
    "dd.service": "policy-service",
    "dd.env": "production",
    "dd.version": "1.2.0",
    "correlation_id": request.state.correlation_id,
    "policy_id": str(policy.id),
})

# ❌ Bad — unstructured print
print(f"Policy {policy.id} created by {user.id}")
```

```java
// ✅ Good — Spring Boot with Logback JSON + MDC
MDC.put("dd.service", "policy-service");
MDC.put("dd.env", "production");
MDC.put("dd.version", "1.2.0");
MDC.put("correlation_id", correlationId);
logger.info("policy_created policy_id={}", policy.getId());

// ❌ Bad — System.out without MDC
System.out.println("Policy created: " + policy.getId());
```

```js
// ✅ Good — Express with pino JSON
const pino = require('pino');
const logger = pino({
  level: 'info',
  formatters: {
    log: (obj) => ({
      ...obj,
      dd: { service: 'policy-service', env: process.env.NODE_ENV, version: '1.2.0' },
    }),
  },
});
logger.info({ correlationId, policyId: policy.id }, 'policy_created');

// ❌ Bad
console.log(`Policy ${policy.id} created`);
```

## Required Schema Fields

Every log must include: `timestamp` (ISO 8601 UTC), `level` (DEBUG/INFO/WARN/ERROR), `message`, `service.name`. Recommended: `trace.id`, `span.id`. Optional: `user.id` (masked), `error.message`, `error.stack`.

## Log ↔ Trace Correlation

Inject `dd.trace_id` and `dd.span_id` into every log line. Enable `DD_LOGS_INJECTION=true` for automatic correlation in Datadog.

```python
# ✅ Good — automatic log injection with ddtrace
# Env: DD_LOGS_INJECTION=true
logger.info("payment_processed", extra={
    "correlation_id": correlation_id,
    "amount": str(amount),
})
# Output will include dd.trace_id and dd.span_id automatically

# ❌ Bad — logs without trace context
logger.info("payment processed")
```

## Log Security

Never log PII, tokens, passwords, or financial data without masking. Use Datadog Sensitive Data Scanner for automatic redaction.

```python
# ✅ Good — masked data
logger.info("policy_accessed", extra={
    "holder_doc": "****5678",
    "policy_id": str(policy.id),
})

# ❌ Bad — exposed PII
logger.info("policy_accessed", extra={
    "holder_doc": "1234565678",
    "holder_email": "[email]",
})
```

## Retention

Logs: 30 days in platform, metadata (timestamp, trace.id, span.id, service.name) 90 days.
