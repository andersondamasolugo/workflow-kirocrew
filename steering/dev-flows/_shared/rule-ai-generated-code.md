---
inclusion: always
---

# AI-Generated Code Safety — Seguros Bolívar

Based on OWASP Top 10 for LLM Applications v2.0, NIST AI 600-1, and Google SAIF. All AI-generated code must meet the same standards as human-written code.

## Treat AI Output as Untrusted Input

Never execute AI-generated code directly in production without human review. Validate logic, security, and alignment with project patterns before integrating.

```python
# ✅ Good — review before integrating
# 1. AI generates the code
# 2. Developer reviews logic and security
# 3. Tests are executed
# 4. PR with review from another developer

# ❌ Bad — copy-paste directly to production without review
```

## Never Expose Secrets in Prompts

Never include API keys, tokens, passwords, PII, or real data in prompts or context sent to the model. Use placeholders.

```python
# ✅ Good — placeholder in the prompt
# "Create a PostgreSQL connection using the DB_PASSWORD environment variable"

# ❌ Bad — real secret in the prompt
# "Create a PostgreSQL connection with password P@ssw0rd123!"
```

## Validate Suggested Dependencies

Verify that every AI-suggested dependency actually exists and is legitimate. Names similar to popular packages may be typosquatting (supply chain attack). If the project uses JFrog, confirm availability in the institutional repository.

```bash
# ✅ Good — verify before installing
# 1. Confirm the package exists in the official registry
# 2. Check active maintenance and popularity
# 3. Pin exact version

# ❌ Bad — install without verifying
pip install fastapi-utils-helper  # does this actually exist?
npm install expres                # typosquatting of express
```

## Never Invent APIs or Libraries

If the model suggests a function, method, or library, verify it exists in the official documentation. LLMs can generate plausible but nonexistent APIs (hallucinations).

```python
# ✅ Good — use documented APIs
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Not found")

# ❌ Bad — API invented by the model
from fastapi import NotFoundException  # does not exist
raise NotFoundException("Not found")
```

## Validate Outputs Before Side Effects

Never execute destructive actions (DB writes, payments, deletions, infra changes) based directly on AI output without explicit validation.

```python
# ✅ Good — validate before executing
async def process_ai_suggestion(suggestion: AISuggestion) -> None:
    validated = validate_against_business_rules(suggestion)
    if requires_human_approval(validated):
        await queue_for_review(validated)
        return
    await execute_action(validated)

# ❌ Bad — execute without validation
async def process_ai_suggestion(suggestion: dict) -> None:
    await db.execute(suggestion["query"])  # dangerous
```

## Never Trust Security by Default

AI-generated code may omit validations, authorization, or sanitization. Verify that all generated code includes:
- Input validation (Pydantic/Zod/Jakarta)
- Permission verification (ownership, RBAC)
- Parameterized queries (never SQL concatenation)
- Specific error handling (never generic catch)

```python
# ✅ Good — AI generates complete secure code
@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id: UUID, user: User = Depends(get_current_user)) -> PolicyResponse:
    policy = await policy_repo.find(policy_id)
    if not policy:
        raise HTTPException(404)
    if policy.owner_id != user.id:
        raise HTTPException(403)
    return PolicyResponse.from_orm(policy)

# ❌ Bad — AI generates code without auth or validation
@app.get("/api/v1/policies/{policy_id}")
async def get_policy(policy_id):
    return await policy_repo.find(policy_id)
```
