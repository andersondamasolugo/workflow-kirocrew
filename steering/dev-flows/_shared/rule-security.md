---
inclusion: always
---

# Secure Coding Rules — Seguros Bolívar

## Global Principles

Apply Security by Design: security is a constraint, not a feature. All input is malicious until validated (Zero Trust Input). Prefer allowlists over blocklists. Apply least privilege in app, DB, cloud, and CI/CD. Generic errors to the user, details only internal. Never hardcode secrets. Never expose more data than necessary.

## Dependencies — Strict Pinning

Pin exact versions on all dependencies. `latest`, `^`, `*` are forbidden. Audit with `npm audit` / `pip-audit` in pipeline. Generate SBOM (CycloneDX or SPDX).

```python
# ✅ Good — strict pinning
# requirements.txt
fastapi==0.128.0
SQLAlchemy==2.0.46

# ❌ Bad — open ranges
fastapi>=0.100
SQLAlchemy~=2.0
```

## Backend Validation and Sanitization

Validate type, format, length, range, enum, and presence on the server ALWAYS. Normalize inputs (trim, unicode). Limit body, header, query param, and file sizes. Reject unexpected keys. Use strict formats (UUID v4, ISO-8601).

```python
# ✅ Good — strict validation with Pydantic
class PolicyRequest(BaseModel):
    policy_id: UUID4
    start_date: date
    coverage: Literal["basic", "premium", "full"]
    amount: condecimal(gt=0, max_digits=12, decimal_places=2)

# ❌ Bad — no validation, accepts anything
@app.post("/api/v1/policies")
async def create(data: dict):
    return await repo.insert(data)
```

## SQL / NoSQL / Command Injection

Use prepared statements / parameterized queries ALWAYS. Never concatenate strings for SQL. In ORMs, never `.raw()` with unsanitized input. For NoSQL, allowlist filterable fields. Never use `exec("cmd " + userInput)` or `shell=True`.

```python
# ✅ Good — parameterized query
result = await db.execute(select(Policy).where(Policy.id == policy_id))

# ❌ Bad — SQL concatenation
result = await db.execute(f"SELECT * FROM policies WHERE id = '{policy_id}'")
```

## SSRF

Allowlist domains/URLs per service. Block private IPs (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.169.254). HTTPS only. Strict timeouts and redirect limits.

## Path Traversal

Never build paths with concatenation. Canonicalize with `realpath` and verify allowed directory. Block `..` and absolute paths. Uploads: validate real MIME type, size, allowlisted extension, store outside webroot, random names.

```python
# ✅ Good — safe path
safe_path = Path(UPLOAD_DIR).joinpath(filename).resolve()
if not str(safe_path).startswith(str(Path(UPLOAD_DIR).resolve())):
    raise HTTPException(403, "Invalid path")

# ❌ Bad — direct concatenation
file_path = f"./uploads/{user_input_filename}"
```

## Authentication and Sessions

MFA where applicable. Short-lived tokens + refresh rotation. Cookies: `Secure` + `HttpOnly` + `SameSite`. Rate limit + lockouts against brute-force.

## Authorization (BOLA/IDOR)

Validate permissions on every request. Never trust client-side IDs. Explicit per-resource verification (owner/tenant/org).

```python
# ✅ Good — explicit ownership verification
@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: UUID, user=Depends(get_current_user)):
    policy = await policy_service.get(policy_id)
    if policy.owner_id != user.id:
        raise HTTPException(403)
    return policy

# ❌ Bad — returns without verifying ownership
@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: UUID):
    return await policy_service.get(policy_id)
```

## XSS and Frontend

In Angular, avoid `[innerHTML]` without sanitizing — use `DomSanitizer` with allowlist. In legacy React projects, forbid `dangerouslySetInnerHTML` unless justified with DOMPurify. Context-aware escaping (HTML/attr/URL/JS). CSRF tokens if using cookies for auth. Never store tokens in `localStorage` — use httpOnly cookies.

## Database Security

Prepared statements mandatory. Separate roles (read/write/admin) per service. Never `root/admin` in production. Encryption at-rest (AES-256) and column-level for PII. TLS in transit always. Encrypted backups with restore tests.

## Security Headers (Mandatory)

Configure HSTS, CSP (block inline scripts), `X-Content-Type-Options: nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`. Force HTTPS and block unused HTTP methods.

## Information Leakage Prevention

No PII/secrets in logs, traces, errors, analytics, or LLM prompts. API responses with allowlisted DTOs, never full objects. Mask sensitive fields (`****1234`). Never expose stack traces to the client.

```python
# ✅ Good — DTO with masking, generic error
class ClientResponse(BaseModel):
    document: str  # "****5678"
    name: str      # "D*** C***"

@app.exception_handler(Exception)
async def handle(req, exc):
    logger.error("unhandled", extra={"correlation_id": req.state.correlation_id, "error": str(exc)})
    return JSONResponse(500, {"detail": "Internal error"})

# ❌ Bad — exposed PII, stack trace to client
return {"document": "1234565678", "error": traceback.format_exc()}
```

## Secure Logging

Never log tokens, passwords, PII, or prompts with secrets. Structured logging with redaction (masking). Correlation IDs for traceability.

## OWASP LLM (If AI Applies)

Separate system/developer/user messages, never mix. Never send PII/secrets to the model — automatic redaction before prompts. Allowlist tools and operations. Validate outputs before executing side effects.
