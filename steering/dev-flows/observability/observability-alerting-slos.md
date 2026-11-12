---
inclusion: auto
name: observability-alerting-slos
description: SLOs/SLIs, burn rate alerts, dashboards, and production readiness guide when working with Datadog monitors, alerts, SLOs, or dashboards.
---

# SLOs, Alerts & Dashboards — Datadog (Seguros Bolívar)

## SLOs and SLIs Required

Every service must have SLOs and SLIs defined before going to production. Define SLOs as code (Terraform/Datadog provider).

```hcl
# ✅ Good — SLO as code with Terraform
resource "datadog_service_level_objective" "availability" {
  name        = "[policy-service] Availability SLO"
  type        = "metric"
  description = "99.9% successful requests over 28 days"

  query {
    numerator   = "sum:trace.fastapi.request.hits{service:policy-service,env:production}.as_count() - sum:trace.fastapi.request.errors{service:policy-service,env:production}.as_count()"
    denominator = "sum:trace.fastapi.request.hits{service:policy-service,env:production}.as_count()"
  }

  thresholds {
    timeframe = "28d"
    target    = 99.9
    warning   = 99.95
  }

  tags = ["service:policy-service", "env:production", "team:policies"]
}

# ❌ Bad — informal SLO without measurable definition
```

## Symptom-Based Alerts (Burn Rate)

High-severity alerts MUST be based on error budget consumption, not isolated infrastructure metrics. Every alert MUST be actionable: real impact, required intervention, link to dashboard and runbook.

- **Fast Burn (P1/P2):** 2% of 28-day error budget consumed in 1 hour → page on-call.
- **Slow Burn (P3/P4):** 10% of 28-day error budget consumed in 3 days → ticket during business hours.

```hcl
# ✅ Good — burn rate alert with actionable context
resource "datadog_monitor" "slo_burn_rate_fast" {
  name    = "[policy-service] SLO Fast Burn Alert"
  type    = "slo alert"
  query   = "burn_rate(\"<slo_id>\").over(\"1h\").long_window(\"1h\").short_window(\"5m\") > 14.4"
  message = <<-EOT
    🔥 Fast burn: policy-service consuming error budget rapidly.
    Impact: users experiencing errors in quotes.
    Dashboard: https://app.datadoghq.com/dashboard/policy-service
    Runbook: https://wiki.internal/runbooks/policy-service-slo-burn
    @pagerduty-policies @slack-team-policies
  EOT

  tags = ["service:policy-service", "env:production", "team:policies", "criticidad:critica", "scope:opsgenie"]
}

# ❌ Bad — cause-based alert, generates fatigue
resource "datadog_monitor" "high_cpu" {
  name  = "CPU > 90%"
  query = "avg(last_5m):avg:system.cpu.user{host:server-1} > 90"
}
```

## Dashboards

Every critical service must have a health dashboard organized in three layers:

- **Business:** CX (NPS, channel errors), TX (sales, renewals), Risk (fraud, alerts).
- **Applications:** Golden Signals (latency p50/p95/p99, error rate, throughput), SLO compliance.
- **Infrastructure:** CPU, memory, disk, network, pods/containers, health checks.

Include template variables to filter by `env`, `service`, `team`, and `platform`.

## Production Readiness

Complete the checklist before going to production:

- [ ] SLOs, SLIs, and KPIs defined and approved
- [ ] Logs, metrics, and traces enabled
- [ ] Operational dashboards in Datadog/Grafana
- [ ] Alerts integrated with Opsgenie with runbooks
- [ ] Complete tagging per corporate policy
- [ ] Resilience and failover tests

## Post-Incident RCA

Every high-severity incident requires a documented RCA within 5 business days. Use observability data (logs, traces, correlated metrics) as evidence.

## Prohibitions

- Never create monitors without a runbook and notification channel.
- Never create high-severity alerts based on causes (CPU, disk) — use burn rate on SLOs.
- Never go to production without defined SLOs/SLIs and completed readiness checklist.
