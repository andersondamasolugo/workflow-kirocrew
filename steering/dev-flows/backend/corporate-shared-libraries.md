---
inclusion: auto
name: corporate-shared-libraries
description: Corporate shared libraries guide when working with error handling, swagger/OpenAPI, parameter store, logging, actuator, or dependency management in Java/Node/Python projects.
---

# Corporate Shared Libraries — Seguros Bolívar

Use corporate libraries instead of custom implementations. These are mandatory for all projects.

## Error Handling Library

Use the centralized error handling library. Never build custom exception hierarchies from scratch.

| Language | Package |
|----------|---------|
| Java | `com.segurosbolivar.commons:error-handling` |
| Node.js | `@segurosbolivar/commons-error-handling` |
| Python | `segurosbolivar-commons-error-handling` |

### Error Categories

| Category | HTTP Code | When to Use |
|----------|-----------|-------------|
| ValidationError | 400 | Input validation failures |
| BusinessError | 422 / 409 | Business rule violations |
| NotFoundError | 404 | Resource not found |
| UnexpectedError | 500 | Unhandled exceptions |

```java
// ✅ Good — Java: declare exception in controller, use @RestControllerAdvice
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BolivarBusinessException.class)
    public ResponseEntity<ErrorResponse> handle(BolivarBusinessException ex) { ... }
}

// ❌ Bad — custom exception hierarchy ignoring corporate library
public class MyCustomException extends RuntimeException { ... }
```

```js
// ✅ Good — Node.js: use corporate error handler middleware
const { ErrorHandler } = require('@segurosbolivar/commons-error-handling');
app.use(ErrorHandler.middleware());

// ❌ Bad — manual error handling without corporate library
app.use((err, req, res, next) => { res.status(500).json({ error: err.message }); });
```

## Swagger / OpenAPI Documentation

Automatic API documentation is mandatory on every service.

| Language | Package |
|----------|---------|
| Java | `com.segurosbolivar.commons:swagger` |
| Node.js | `swagger-jsdoc` + `swagger-ui-express` |
| Python | FastAPI built-in (`/docs`) |

### Java Swagger Rules

- Set `springdoc.api-docs.path: srv-<domain>-openapi` matching context-path.
- Annotate controllers with `@Tag(name, description)`.
- Annotate methods with `@Operation(summary, description)` — description must specify the consumed procedure/service.
- Use `@ApiResponses` with minimum three codes: 200, 400, 500.
- Annotate all parameters with `@Parameter(name, description, required)`.
- Annotate request/response classes with `@Schema(name, description)`.

```java
// ✅ Good — fully documented endpoint
@Tag(name = "Policies", description = "Policy management operations")
@RestController
public class PolicyController {

    @Operation(summary = "Get policy by ID", description = "Consumes sp_get_policy procedure")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Policy found",
            content = @Content(schema = @Schema(implementation = PolicyResponse.class))),
        @ApiResponse(responseCode = "400", description = "Invalid request",
            content = @Content(schema = @Schema(implementation = ExceptionModel.class))),
        @ApiResponse(responseCode = "500", description = "Internal error",
            content = @Content(schema = @Schema(implementation = ExceptionModel.class)))
    })
    public PolicyResponse getPolicy(@Parameter(name = "id", description = "Policy ID", required = true) UUID id) { ... }
}

// ❌ Bad — no annotations, undocumented API
@GetMapping("/{id}")
public PolicyResponse getPolicy(UUID id) { ... }
```

### Verification Checklist

Swagger UI must load at `host:port/domain/swagger-ui.html` showing: API name, version, OAS 3.0, description, servers, methods, and schemas.

## Parameter Store

All external configuration (DB credentials, API keys, tokens) must come from AWS SSM Parameter Store. Never hardcode.

| Language | Package |
|----------|---------|
| Java | `com.segurosbolivar.commons:parameter-store` |
| Node.js | `@segurosbolivar/commons-parameter-store` |
| Python | `segurosbolivar-commons-parameter-store` |

```java
// ✅ Good — Java: build DB URL from Parameter Store
@Configuration
public class DataBaseConfiguration {
    @Autowired
    private ParameterStoreSource parameterStoreSource;

    public String getDbUrl() {
        return parameterStoreSource.getProperty(prefix + "/db/url");
    }
}

// ❌ Bad — hardcoded connection string
private static final String DB_URL = "jdbc:postgresql://prod-db:5432/mydb";
```

```python
# ✅ Good — Python: cache Parameter Store values
from functools import lru_cache

@lru_cache
def get_db_config() -> dict:
    return parameter_store.get_parameters("/myapp/prod/db")

# ❌ Bad — fetch on every request without caching
```

All values used in configuration classes must be declared in `application.yaml` (Java).

## Actuator (Java Only)

Health check and monitoring endpoints are mandatory for Java services.

```yaml
# ✅ Good — application.yaml
management:
  endpoints:
    web:
      exposure:
        include: health, mappings
      base-path: /
info:
  status: UP
```

Verify: `host:port/domain/health` returns 200 and `host:port/domain/mappings` returns the endpoint map.

## Centralized Logging Library

Use the corporate logging library for structured JSON logs with correlation IDs.

| Language | Package |
|----------|---------|
| Java | Log4j 2.17+ |
| Node.js | `@segurosbolivar/commons-logging` |
| Python | `segurosbolivar-commons-logging` or `logging` |

Every log entry must include `requestId`, `correlationId`, and `serviceName`. Labels and messages must be mapped in properties/resources files (Java/Node.js).

```java
// ✅ Good — structured log with correlation
logger.info("policy_created", Map.of("correlationId", correlationId, "policyId", policyId));

// ❌ Bad — System.out.println
System.out.println("Policy created: " + policyId);
```

## SQL Injection Prevention (Java)

Use `com.segurosbolivar.commons:comunes-security-sql` for SQL injection prevention in Java projects that use raw queries.

## MyBatis (Java — Optional)

For stored procedure calls, use `com.segurosbolivar.commons:mybatis`. Annotate IN parameter classes with `@BolivarObject(objectName)` and nested fields with `@BolivarField(fieldName)`.

## Dependency Management

Download all dependencies exclusively from the institutional **JFrog** repository. Pin exact versions — no floating ranges (`^`, `~`, `*`, `latest`).

```groovy
// ✅ Good — Java: JFrog repo + pinned version
repositories {
    maven { url "https://<tu-host-jfrog>/artifactory/libs-release" }
}
dependencies {
    implementation 'com.segurosbolivar.commons:error-handling:1.2.0'
}

// ❌ Bad — Maven Central + floating version
dependencies {
    implementation 'com.segurosbolivar.commons:error-handling:+'
}
```

`gradle.properties` must NOT contain JFrog credentials — pipelines inject them automatically.
