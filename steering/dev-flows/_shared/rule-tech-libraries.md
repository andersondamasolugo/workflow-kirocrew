---
inclusion: always
---

# Approved Libraries by Stack

Prefer libraries from each stack's ecosystem. Mixing ecosystems introduces unnecessary complexity, conflicting patterns, and maintenance burden.

## Backend — Dependency Selection

Use only these libraries per stack. Each was selected for institutional support, security compliance, and CI/CD compatibility.

| Concern         | Spring Boot              | FastAPI                | Express                | Fastify                |
|-----------------|--------------------------|------------------------|------------------------|------------------------|
| ORM             | Spring Data JPA          | SQLAlchemy / Tortoise  | pg (node-postgres)     | pg (node-postgres)     |
| Validation      | Jakarta Validation       | Pydantic               | Zod / Joi              | Zod / Joi              |
| Auth            | Spring Security          | FastAPI Security       | Passport.js + JWT      | Passport.js + JWT      |
| Security        | Spring Security          | —                      | Helmet + CORS          | Helmet + CORS          |
| File Upload     | Spring Multipart         | python-multipart       | Multer                 | @fastify/multipart     |
| Password Hash   | BCryptPasswordEncoder    | passlib / bcrypt       | bcrypt                 | bcrypt                 |
| Testing         | JUnit 5 + MockMvc        | pytest + httpx         | Jest + Supertest       | Jest + Supertest       |
| Migrations      | Flyway / Liquibase       | Alembic                | node-pg-migrate        | node-pg-migrate        |
| Dep Manager     | Gradle 8.x / Maven 3.9+ | Poetry 1.8+            | npm 10.x+             | npm 10.x+             |
| DB Adapter      | JDBC / HikariCP          | psycopg2 / asyncpg     | pg                     | pg                     |

```python
# ✅ Good — use the approved library for your stack
from pydantic import BaseModel  # FastAPI validation
from sqlalchemy import select    # FastAPI ORM

# ❌ Bad — mixing ecosystems
from marshmallow import Schema   # not approved for FastAPI, use Pydantic
from peewee import Model         # not approved, use SQLAlchemy
```

## Angular — Approved Libraries

Angular has most tools built-in. Avoid adding external libraries for concerns Angular already covers.

| Concern | Library |
|---------|---------|
| HTTP | HttpClient (built-in) |
| Reactive | RxJS (built-in) |
| CLI | Angular CLI |
| Testing | Jest |
| DI Pattern | inject() (v17+) |

```ts
// ✅ Good — Angular with inject() and built-in HttpClient
export class UserService {
  private http = inject(HttpClient);
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>('/api/users');
  }
}

// ❌ Bad — using axios in Angular (use HttpClient instead)
import axios from 'axios';
const res = await axios.get('/api/users');
```

## React — Approved Libraries

React projects must use these libraries for consistency across teams. Using unapproved alternatives fragments the codebase and makes cross-team collaboration harder.

| Concern | Library | Version |
|---------|---------|---------|
| Build Tool | Vite | 5.x |
| Routing | react-router-dom | 6.x |
| Server State | @tanstack/react-query | 5.x |
| Forms | React Hook Form + @hookform/resolvers + Zod | 7.x / 3.x |
| HTTP Client | Axios | 1.x |
| Styling | Tailwind CSS + tailwind-merge + clsx + cva | 3.x |
| UI Components | Shadcn UI + Radix UI | Latest |
| Icons | Lucide React | Latest |
| Charts | Recharts | 2.x |
| PDF | jsPDF + jspdf-autotable | 3.x |
| HTML to Image | html2canvas | 1.x |
| Toasts | Sonner | 1.x |
| Date Picker | react-day-picker | 8.x |
| Testing | Vitest 3.x + React Testing Library 16.x | — |

```tsx
// ✅ Good — React with approved libraries
import { useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// ❌ Bad — unapproved alternatives
import { useSelector } from 'react-redux';  // use React Query instead
import { Formik } from 'formik';            // use React Hook Form instead
```
