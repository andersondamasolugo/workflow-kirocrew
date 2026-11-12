---
inclusion: always
---

# Architecture Rules

## Consistency

Replicate the existing standard pattern before modifying code. Never invent new patterns or do "vibe coding". Inconsistent patterns increase onboarding time and make critical fixes slower.

```
// ✅ Good — follows the existing project pattern
class UserService {
    constructor(private repo: UserRepository) {}
}

// ❌ Bad — invents a different pattern
class UserService {
    repo = new UserRepository(); // implicit singleton without injection
}
```

## Layer Separation

Structure in independent layers. Mixing responsibilities creates tightly coupled systems that are hard to test and scale.

- **Presentation (Frontend):** UI and events only. NEVER business logic.
- **Logic (Backend/API):** Domain rules, calculations, and validations.
- **Persistence (Data):** Connection always via API, never direct from frontend. Two data sources are available: operational APIs (real-time, direct from source systems) and Data Operativa APIs (consolidated from the Data Lake via GraphQL, with synchronization latency). Choose based on data freshness requirements.
- **Usability:** When a frontend exists, prioritize minimal user interaction paths. Fewer steps reduce user errors and abandonment.

```
// ✅ Good — logic in the backend
POST /api/v1/quotes → validate rules → calculate → return response

// ❌ Bad — calculatePremium() inside a UI component
```

## Security Architecture Decisions

These are architectural constraints — for implementation details, see `rule-security.md`.

- All inter-service communication must be authenticated (JWT signed by institutional IdP). Unauthenticated calls allow lateral movement.
- Authorization is a backend responsibility — never client-side. Client checks are trivially bypassed.
- API responses must mask all PII, financial, and health data. Regulatory compliance (Habeas Data) requires it.
- Secrets managed via Secret Manager or env vars, never in code. Leaked repo secrets are the #1 breach cause.
- Communication via DNS only — no static IPs. IPs change across environments.
- No tokens in `localStorage` — use `httpOnly` cookies. localStorage is XSS-accessible.
- Strict typing on all fields. Untyped inputs enable injection attacks.
- Data retention: max 90 days for sensitive data. Regulatory requirement.

```
// ✅ Good — backend validates authorization
GET /api/v1/policies → extract user from JWT → validate scope "policies:read" → return filtered data

// ❌ Bad — frontend decides permissions
if (user.role === "admin") showAllPolicies();  // client-side, trivially bypassed
```

> Implementation details, secure coding patterns, and OWASP guidelines: see `rule-security.md`.

## Resilience

Implement circuit breakers on all external calls — without them, one failing dependency cascades and takes down the system. Long-running tasks must execute in the background — synchronous heavy operations block threads and cause timeouts. Not all operations require async patterns — for short transactions, prefer fail-fast with low timeouts so failures are immediate and explicit rather than queued. Apply rate limiting to protect core components — without it, a single client can exhaust resources.

```
// ✅ Good — circuit breaker with fallback
circuitBreaker(action: → externalClient.post(url, payload),
               fallback: → cachedResponse, failureThreshold: 5, recoveryTimeout: 30s)

// ✅ Good — async for heavy operations
POST /api/v1/reports → enqueue job → return 202 Accepted with job ID

// ✅ Good — fail-fast for short transactions (low timeout, no queue)
POST /api/v1/quotes → timeout: 3s → if fails, return error immediately

// ✅ Good — rate limiting
GET /api/v1/quotes → max 100 req/min per client → 429 with Retry-After

// ❌ Bad — no protection, no timeout strategy
```

## Performance Architecture Decisions

Without explicit SLOs, teams cannot measure if their service performs acceptably.

- Reference targets: frontend < 3s, internal APIs < 15s. Baselines, not hard limits.
- Each service must define and document its own SLOs based on its dependency chain.
- External integrations must document: provider SLA, timeout, and fallback.
- Operations exceeding targets must use async patterns or user feedback (progress indicators).
- Critical bugs: 1 business day. Non-critical: 5 business days.

```
// ✅ Good — SLO: p95 < 2s, external dep timeout: 3s, fallback: cached rates
// ❌ Bad — no SLO, no timeout on external call
```

## Observability

Insert `Correlation-ID` in every inter-service request — without it, tracing across services is impossible. Send structured logs to centralized services only — local logs are lost on container restart.

```
// ✅ Good
log.info("policy_created", { correlation_id: req.correlationId, policy_id: policy.id })

// ❌ Bad
print("Policy created: " + policy.id)  // no structure, no correlation
```

## API Contracts and Versioning (API First)

Version routes with a prefix — without it, schema changes break all consumers. Every API must have an OpenAPI spec as source of truth. Maintain backward compatibility during deprecation. Communicate sunset dates before removal.

```
// ✅ Good
/api/v1/policies  → OpenAPI spec defines schema
/api/v2/policies  → backward compatible during transition

// ❌ Bad
/api/policies  // no version, no contract
```

## AI First

Every new service must be designed for AI integration. AI agents need structured, predictable APIs — unstructured responses cause parsing failures. Design composable endpoints for AI orchestrators. AI inference must be asynchronous. Log all AI inputs/outputs. Version models. Never send PII — apply redaction. For similarity search, use PgVector or Pinecone.

```
// ✅ Good — AI-consumable endpoint with structured output
POST /api/v1/claims/analyze
  Response: { "risk_score": 0.82, "category": "auto", "suggested_action": "review" }

// ❌ Bad — unstructured response
POST /api/v1/claims/analyze
  Response: "The claim looks risky, probably should review it"
```

> AI-generated code safety, hallucination prevention, and OWASP LLM guidelines: see `rule-ai-generated-code.md`.

## IT Governance

Download libraries exclusively from JFrog — public registries expose the supply chain to typosquatting. Code in the official repository. Environments (Dev, Stage, Prod) physically separated — shared environments cause data leaks. Implement graceful shutdown. Use only the approved technology stack.

> Approved stacks, forbidden technologies, and legacy exceptions: see `rule-tech-stack.md`.

```
// ✅ Good — graceful shutdown
onShutdownSignal: → stop new requests → complete pending transactions → close connections → exit

// ❌ Bad — abrupt shutdown without completing transactions
```
