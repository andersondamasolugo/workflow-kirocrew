---
inclusion: always
---

# Code Style — Clean Code (Seguros Bolívar)

## Guiding Principles

Code must be human-readable first, machine-executable second. Apply DRY, SOLID, and KISS. If you need a comment to explain what the code does, rewrite the code. Use comments only to explain "why" and non-obvious decisions.

```python
# ✅ Good — name explains intent
def calculate_premium_for_policy(policy: Policy, risk: RiskProfile) -> Decimal:
    base = policy.coverage_amount * risk.factor
    return base + calculate_tax(base)

# ❌ Bad — generic name, needs comment
def calc(p, r):  # calculates premium
    x = p.ca * r.f  # base
    return x + tax(x)  # with tax
```

## Naming Conventions

### General Rules

| Element | Java / JS / TS | Python |
|---------|---------------|--------|
| Classes / Interfaces | PascalCase | PascalCase |
| Methods / Functions | camelCase | snake_case |
| Variables | camelCase | snake_case |
| Constants | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE |
| Booleans | `isActive`, `hasPermission` | `is_active`, `has_permission` |
| Files | PascalCase (Java), PascalCase classes / camelCase utils (Node/TS) | snake_case |
| Packages / Folders | lowercase | lowercase |

### Python (FastAPI)

```python
# ✅ Good
class PolicyResponse(BaseModel):
    policy_id: UUID4
    is_active: bool
    holder_name: str

MAX_RETRY_ATTEMPTS = 3

async def get_active_policies(user_id: UUID) -> list[PolicyResponse]:
    ...

# ❌ Bad
class policyresponse(BaseModel):
    PolicyId: str
    active: bool
```

### Java (Spring Boot)

```java
// ✅ Good
public class PolicyService {
    private static final int MAX_RETRY_ATTEMPTS = 3;

    public PolicyResponse findActivePolicy(UUID policyId) {
        ...
    }
}

// ❌ Bad
public class policy_service {
    public PolicyResponse FindActivePolicy(String id) { ... }
}
```

### Node.js (Express / Fastify)

Files in `kebab-case.js`. Classes in PascalCase files.

```js
// ✅ Good — policy-service.js
const MAX_RETRY_ATTEMPTS = 3;

const findActivePolicy = async (policyId) => {
  ...
};

// ❌ Bad — PolicyService.js
var find_active_policy = function(id) { ... }
```

### Lambda Naming

Lambda name in lowercase; use camelCase for compound names. Handler class must include a comment with the local test request and a short description.

### Microservice Naming

Repository format: `comunes-<domain>-ms`. Operation package names in lowercase with infinitive verbs (e.g. `consultarDatos`, `registrarPoliza`).

### REST API Path Convention

Structure: `/domain/layer/version/functionality*/entity`. Layer is `api`, `composicion`, or `lambda`. Must be camelCase or all lowercase — no special characters.

```python
# ✅ Good
"/seguros/api/v1/polizas/datosBasicos"

# ❌ Bad
"/api/Seguros/Polizas"  # PascalCase, no version, no layer
```

## Mandatory Type Safety

Type hints in Python, strict types in Java, JSDoc or TypeScript in Node. Never `any`, `Object`, or untyped `dict`.

```python
# ✅ Good
async def create_policy(request: PolicyRequest, user: User = Depends(get_current_user)) -> PolicyResponse:
    ...

# ❌ Bad
async def create_policy(request, user):
    ...
```

```js
// ✅ Good — JSDoc with types
/** @param {import('./types').PolicyRequest} req */
const createPolicy = async (req) => { ... };

// ❌ Bad — no type documentation
const createPolicy = async (req) => { ... };
```

## Functions: Small and Single-Purpose

Maximum ~20 lines per function. One function does one thing. If it has `and` in the name, split it. Maximum 3 parameters; use an object/model for more. Maximum cyclomatic complexity per method: 15.

```python
# ✅ Good — small functions with clear purpose
async def validate_policy(data: PolicyRequest) -> PolicyRequest:
    validate_coverage_limits(data)
    validate_holder_age(data.holder_birth_date)
    return data

# ❌ Bad — giant function that does everything
async def process_policy(data: dict) -> dict:
    # 80 lines of validation, calculation, persistence, and notification
    ...
```

## Error Handling

Specific errors, never bare `except Exception` in business logic. Descriptive error messages internally, generic to the client. Fail fast: validate early.

```python
# ✅ Good — specific error, fail fast
async def get_policy(policy_id: UUID, user: User) -> Policy:
    policy = await policy_repo.find(policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)
    if policy.owner_id != user.id:
        raise ForbiddenError("Access denied")
    return policy

# ❌ Bad — generic catch, silent error
async def get_policy(policy_id, user):
    try:
        return await policy_repo.find(policy_id)
    except:
        return None
```

```js
// ✅ Good — Express with explicit error handling
app.get('/api/policies/:id', async (req, res, next) => {
  try {
    const policy = await policyService.findById(req.params.id);
    if (!policy) return res.status(404).json({ detail: 'Not found' });
    res.json(policy);
  } catch (err) {
    next(err);
  }
});
```

## File Structure

Group by domain/feature, not by technical type. Each module with clear responsibility.

```
# ✅ Good — grouped by domain
src/
  policies/
    policy_router.py
    policy_service.py
    policy_repository.py
    policy_models.py
  claims/
    claim_router.py
    claim_service.py

# ❌ Bad — grouped by technical type
src/
  controllers/
  services/
  models/
  repositories/
```

## Imports and Dependencies

Order imports: stdlib → third-party → local. Do not import entire modules if you only use one function. No circular imports.

```python
# ✅ Good — ordered and specific imports
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.policies.policy_service import PolicyService
```

## No Dead Code

Remove commented-out code, unused functions, unreferenced imports. Git is the history, not comments.

## Code Documentation

Every internal method must have a short description including parameter descriptions and return value. Use JSDoc (JS/TS), Javadoc (Java), or docstrings (Python).

```python
# ✅ Good — docstring with purpose
async def calculate_premium(policy: Policy) -> Decimal:
    """Calculate the insurance premium based on base amount and factor."""
    return policy.base_amount * PREMIUM_FACTOR

# ❌ Bad — no documentation on non-obvious logic
async def calc(p):
    return p.ba * PF
```

```java
// ✅ Good — Javadoc
/**
 * Finds active policies for a given user.
 * @param userId the user's unique identifier
 * @return list of active policies
 */
public List<PolicyResponse> findActivePolicies(UUID userId) { ... }
```

## SonarQube Compliance

Minimum 80% coverage on business logic. Zero critical or blocker issues. Maximum cyclomatic complexity: 15 per method.

Coverage exclusions (`sonar.coverage.exclusions`): `test`, `models`, `dao`, `repository`, `dto`, `config`, `utils`, `messages`, `resources`, `interfaces`.

## .gitignore Requirements

| Stack | Must exclude |
|-------|-------------|
| Java | `.idea`, `bin`, `build` |
| Node.js | `.idea`, `node_modules`, `.vscode`, `dist` |
| Python | `.idea`, `node_modules`, `.vscode`, `dist`, `__pycache__`, `.pytest_cache` |

## Testing Patterns

Follow **Given / When / Then** (Arrange / Act / Assert). Minimum 80% coverage. All tests must pass before merging. Mock all external dependencies — never consume real backends in tests.

```python
# ✅ Good — Given/When/Then with mock
async def test_get_policy_returns_not_found():
    # Given
    policy_repo.find = AsyncMock(return_value=None)
    # When
    response = await client.get("/api/v1/policies/fake-id")
    # Then
    assert response.status_code == 404
```

A `postmanCollections/` folder must exist at the project root with collection files for each operation.

## README Requirements

Each operation must have a README with: Title, Description, API Path, Request/Response examples, Architecture, Built With, Endpoints, Authors. The repository-level README must list all functionalities.

## Performance

Prioritize readability and correctness first. Profile before optimizing. Use connection pooling for database and external service connections. Cache frequently accessed configuration and reference data.
