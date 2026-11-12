---
inclusion: always
---

# Tech Stack Constraints

## Approved Runtimes

All projects must use one of these runtimes. Version minimums ensure access to security patches and modern language features.

| Runtime | Minimum Version | Use Case |
|---------|----------------|----------|
| Node.js | 20.x (LTS) | Backend services with Express or Fastify |
| Java | JDK 21 (LTS) | Enterprise backend with Spring Boot |
| Python | 3.12+ | APIs with FastAPI, AI/ML workloads |

## Frontend — Angular and React

Angular is the standard for corporate web applications. React is the standard for dynamic, high-performance interfaces. Both are approved for new projects — choose based on project requirements.

```ts
// ✅ Good — Angular (corporate apps with modular architecture)
import { Component } from '@angular/core';

@Component({
  selector: 'app-user-list',
  templateUrl: './user-list.component.html',
})
export class UserListComponent {}

// ✅ Good — React (dynamic interfaces)
import { useQuery } from '@tanstack/react-query';

export const UserList = () => {
  const { data } = useQuery({ queryKey: ['users'], queryFn: fetchUsers });
  return <div>{/* render users */}</div>;
};

// ❌ Bad — Vue, Svelte, or any other frontend framework
import { createApp } from 'vue';
```

Angular projects: use Angular CLI, RxJS, and HttpClient. React projects: use Vite 5.x as build tool, React Router 6.x, React Query 5.x, and Axios 1.x.

## Backend — Java/Spring Boot, Python/FastAPI, or Node.js/Express+Fastify

Use Java with Spring Boot, Python with FastAPI, or Node.js with Express or Fastify. These are the only stacks with institutional support, CI/CD templates, and security baselines. FastAPI is preferred for new Python APIs. Fastify 4.x is optional for high throughput.

```python
# ✅ Good — approved backend stack
from fastapi import FastAPI
app = FastAPI()

# ❌ Bad — unapproved backend framework
from flask import Flask  # forbidden
from django.http import JsonResponse  # forbidden
```

## Approved Databases

PostgreSQL is the standard relational database — it has institutional DBA support and managed infrastructure. MongoDB is approved for unstructured data. Vector databases are approved for AI/ML workloads.

| Database | Version | Use Case |
|----------|---------|----------|
| PostgreSQL | 15+ | Standard relational DB for all services |
| PgVector | (PostgreSQL extension) | Vector search on existing PostgreSQL instances |
| MongoDB | 7.0+ | Unstructured/document data when relational model doesn't fit |
| Pinecone | Managed | Dedicated vector database for AI/ML similarity search |

```python
# ✅ Good — PostgreSQL with approved adapter
engine = create_engine(os.environ["DATABASE_URL"])  # PostgreSQL

# ❌ Bad — MySQL, MariaDB, or unapproved databases
engine = create_engine("mysql://...")
```

## Data Operativa — GraphQL APIs

Operational data from the Data Lake is consumed exclusively through GraphQL APIs. Direct queries bypass access controls, caching, and schema governance. These APIs are the standard interface for accessing consolidated business data.

```graphql
# ✅ Good — consume data via GraphQL API
query GetPolicyMetrics($dateRange: DateRange!) {
  policyMetrics(range: $dateRange) {
    totalPolicies
    activePolicies
  }
}

# ❌ Bad — direct BigQuery or Data Lake queries from application code
```

## Forbidden Stacks

Never use or suggest these technologies. They lack institutional CI/CD support, security baselines, and DBA/infra backing. Explain the constraint and offer the allowed alternative.

- **Frontend**: Vue, Svelte, SolidJS, Next.js, Nuxt, Astro
- **Backend**: NestJS, Go/Gin, Ruby on Rails, Django, Flask, .NET

```ts
// ✅ Good — use approved stack
import { Component } from '@angular/core';  // Angular
import { useQuery } from '@tanstack/react-query';  // React

// ❌ Bad — forbidden frameworks
import { createApp } from 'vue';
import { Controller } from '@nestjs/common';
```

## Dependency Registry

All dependencies must be downloaded from the institutional JFrog Artifactory repository. This ensures supply chain security and license compliance. Configure `.npmrc` (Node.js), `settings.xml` (Maven), or `pyproject.toml` (Poetry) to point to JFrog.

## Legacy Stacks — Maintenance Only

These technologies exist in legacy systems. Maintain them but never start new projects with them. Starting new projects on legacy stacks increases technical debt and lacks institutional support.

| Technology | Context | Rule |
|---|---|---|
| PHP | Legacy web applications | Maintain only. New features must be built in approved stacks. |
| Oracle DB | Core insurance platform (historical) | Read-only access via APIs. New services must use PostgreSQL. |

```
// ✅ Good — maintaining an existing PHP project, follow its patterns
// ❌ Bad — starting a new project in PHP or creating new Oracle schemas
```

> For approved libraries per stack, see `rule-tech-libraries.md`.
