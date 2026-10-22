<!-- docs/README.md -->
# Mini E-commerce REST API

A production-lean REST API for a mini e-commerce platform built with **Node.js, Express.js 5, TypeScript, SQLite, Prisma 6, and Zod 4**. It follows a strict layered architecture (routes → controllers → services → repositories), uses integer cents for money, enforces role-based access control, and makes checkout + stock restoration safe under concurrency.

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Database & migrations](#database-&-migrations)
- [API overview](#api-overview)
- [Error handling](#error-handling)
# PR Title: feat(mini-ecommerce): scaffold API, Prisma schema, error handling, tests, Docker

## Description
- Added mini-ecommerce-app with layered architecture (routes/controllers/services/repositories), core errors/response/logger, middleware (request-context), modules (health), config (env/prisma), types
- Prisma schema with User, Product, Cart/CartItem, Order/OrderItem (snapshots), StockMovement, enums (Role, OrderStatus, StockReason); migrations applied
- App factory with helmet/cors/pino-http/requestContext; centralized error handler (AppError/Zod/Prisma/JSON); 404
- Health endpoints (/api/v1/health, /api/v1/health/ready)
- Seed script with admin/customer and 15 products
- Jest split (unit/integration) with Supertest, global setup running prisma migrate deploy, SQLite WAL/busy_timeout/foreign_keys
- Dockerfile multi-stage, docker-compose (api + test profile), .env.example, ESLint/Prettier/tsconfig

## Verification
- npm run typecheck: clean
- npx eslint .: clean
- npx jest: 5 suites, 18 tests passed
- Dev server: GET /api/v1/health 200; GET /api/v1/health/ready DB up; GET /api/v1/nope returns standard 404 envelope with requestId

## Notes
- Money stored as integer cents; order items snapshot price/SKU/name
- Stock restoration guarded by `stockRestoredAt` (exactly-once) for eligible cancellations
- SQLite busy_timeout + WAL configured

- [Testing](#testing)
- [Docker](#docker)
- [Design decisions](#design-decisions)
- [Scripts](#scripts)
- [License](#license)

## Features

| Area | Details |
|---|---|
| **Auth** | Registration/login with `bcryptjs` (12 rounds), JWT (HS256), roles (`CUSTOMER`, `ADMIN`). Login rate-limited. |
| **Products** | CRUD, unique SKU, `priceCents` (integer), `stock`, `active` flag (soft delete), search (`q`), filters (`minPrice`, `maxPrice`, `inStock`), pagination/sorting. Only admins manage products; inactive products hidden from public listing. |
| **Cart** | Add/update/remove items, per-user ownership enforced, totals computed server-side. |
| **Orders** | Checkout (atomic transaction), order history, admin status management, cancellation with stock restoration. |
| **Inventory safety** | Conditional `UPDATE ... WHERE stock >= qty` to prevent overselling; checkout in one `prisma.$transaction`; exactly-once restock via `stockRestoredAt` compare-and-swap; append-only `StockMovement` ledger. |
| **Security** | Zod validation at all boundaries, ownership checks, role-based authorization, login rate limit, centralized errors, no stack leaks, security headers via `helmet`, CORS configurable. |
| **Docs/tests** | OpenAPI/Swagger (Stage 5), Jest + Supertest, integration tests against real SQLite migrations, Docker Compose for local dev. |

## Architecture

```
src/
├── app.ts                # createApp() factory (test-friendly)
├── server.ts             # bootstrap, graceful shutdown
├── config/               # env.ts (zod-validated), prisma.ts (singleton + SQLite PRAGMAs)
├── core/                 # errors.ts, error-handler.ts, response.ts, logger.ts
├── middleware/           # auth.ts, validate.ts, rate-limit.ts, request-context.ts, not-found.ts
├── modules/              # auth, users, products, cart, orders (routes/controllers/services/repositories/schemas)
├── docs/openapi.ts       # OpenAPI generated from Zod schemas
└── utils/

prisma/
├── schema.prisma
└── migrations/           # checked-in SQL

tests/
├── setup/                # test-env, global/integration/unit setup
├── helpers/              # factories, database reset
├── unit/                 # mocked-service/unit rules
└── integration/          # supertest + real DB
```

**Rule:** `route → controller (HTTP only) → service (business rules) → repository (Prisma)`. Services throw `AppError`s; repositories never build HTTP responses.

## Tech stack

| Category | Package | Notes |
|---|---|---|
| Runtime | Node.js 24, TypeScript 5.9 | `isolatedModules`, strict mode |
| Web | Express 5.3 | `trust proxy` enabled |
| ORM | Prisma 6.19 + SQLite | WAL, `busy_timeout=5000`, `foreign_keys=ON`, `connection_limit=1` |
| Validation | Zod 4.6 | single source of truth for OpenAPI |
| Auth | jsonwebtoken 9, bcryptjs 3 | HS256, 12 rounds (configurable) |
| Security/Middleware | helmet, cors, express-rate-limit 8, pino-http | login rate-limited |
| Docs | swagger-ui-express 5 | `/api/v1/docs`, `/api/v1/docs.json` |
| Tests | Jest 30, ts-jest 29, Supertest 7 | unit + integration projects |

## Getting started

### Prerequisites
- Node.js >= 20.11 (tested with 24.12.0)
- npm >= 9

### Install & run (local)

```bash
cd mini-ecommerce-app
cp .env.example .env
npm ci
npx prisma generate
npx prisma migrate dev
npm run prisma:seed   # optional: admin@shop.local / Password123!, customer@shop.local / Password123!
npm run dev           # http://127.0.0.1:3000/api/v1
```

### Quick smoke test

```bash
# Health
curl -s http://127.0.0.1:3000/api/v1/health
curl -s http://127.0.0.1:3000/api/v1/health/ready

# Unknown route (standard envelope)
curl -s http://127.0.0.1:3000/api/v1/nope
```

## Environment variables

Copy `.env.example` to `.env`. **Never commit real secrets.**

| Variable | Default | Notes |
|---|---|---|
| `NODE_ENV` | `development` | `development` \| `test` \| `production` |
| `PORT` | `3000` | HTTP port |
| `HOST` | `0.0.0.0` | Bind address |
| `DATABASE_URL` | `file:./dev.db?connection_limit=1` | SQLite path/params |
| `JWT_SECRET` | — | **required**, min 32 chars. Refused in production if it equals the example value. |
| `JWT_EXPIRES_IN` | `1h` | e.g. `1h`, `7d` |
| `BCRYPT_ROUNDS` | `12` | 4–15 |
| `LOGIN_RATE_LIMIT_WINDOW_MS` | `900000` | 15 min |
| `LOGIN_RATE_LIMIT_MAX` | `5` | max login attempts per window per IP |
| `CORS_ORIGIN` | `*` | comma-separated origins or `*` |
| `LOG_LEVEL` | `info` | pino levels |

## Database & migrations

- **Migrations are checked in** (`prisma/migrations/`). Integration tests run `prisma migrate deploy` from scratch.
- **SQLite notes:** `PRAGMA journal_mode = WAL`, `PRAGMA busy_timeout = 5000`, `PRAGMA foreign_keys = ON`. `connection_limit=1` helps avoid `SQLITE_BUSY` in dev/test. SQLite `contains` is ASCII-case-insensitive (note for search).
- **Money:** `priceCents` and `totalCents` are integers. No floating point arithmetic.
- **Snapshots:** `OrderItem` copies `sku`, `name`, `unitPriceCents` at checkout time so product edits don't affect history.
- **Soft delete:** `Product.active=false` preserves order history; public endpoints hide inactive products.
- **Audit:** `StockMovement` records every stock delta (`RESERVATION`, `RESTOCK`, `ADJUSTMENT`) with optional `orderId`.

## API overview

Base path: `/api/v1`

| Method | Path | Auth | Notes |
|---|---|---|---|
| `GET` | `/health`, `/health/ready` | public | liveness/readiness |
| `POST` | `/auth/register` | public | create account (default `CUSTOMER`) |
| `POST` | `/auth/login` | public | **rate-limited**; returns JWT |
| `GET` | `/auth/me` | user | current user |
| `GET` | `/users/me` | user | profile (optional PATCH later) |
| `GET` | `/products` | public | `q`, `minPrice`, `maxPrice`, `inStock`, `sort` (`price_asc\|price_desc\|name_asc\|name_desc\|created_desc`), `page`, `limit` (max 100) |
| `GET` | `/products/:id` | public | inactive hidden from non-admins? (public sees active only) |
| `POST`/`PATCH`/`DELETE` | `/products`, `/products/:id` | **admin** | SKU unique, soft delete on DELETE (or hard? see decisions) |
| `GET`/`DELETE` | `/cart` | owner | clear cart |
| `POST`/`PATCH`/`DELETE` | `/cart/items`, `/cart/items/:productId` | owner | add/update/remove; quantity >= 1 |
| `POST` | `/orders/checkout` | owner | atomic transaction; clears cart; snapshots items; reserves stock |
| `GET` | `/orders`, `/orders/:id` | owner | customer sees own; admin can view any |
| `POST` | `/orders/:id/cancel` | owner/admin (rules) | eligible statuses only; **restores stock exactly once** |
| `PATCH` | `/orders/:id/status` | **admin** | transition rules enforced by service |
| `GET` | `/docs`, `/docs.json` | public | Swagger UI / OpenAPI 3.1 (Stage 5) |

**Pagination envelope:** `{ "success": true, "data": [...], "meta": { "pagination": { "page": 1, "limit": 20, "total": 45, "totalPages": 3, "hasNext": true, "hasPrev": false } } }`

## Error handling

All errors use the standard envelope:

```json
{ "success": false, "error": { "code": "ERROR_CODE", "message": "...", "details": [] }, "requestId": "..." }
```

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Zod/body/JSON validation failure |
| 401 | `UNAUTHORIZED` | missing/invalid/expired JWT |
| 403 | `FORBIDDEN` | authenticated but wrong role/privilege |
| 404 | `NOT_FOUND` | resource/route not found (ownership hidden as 404 when appropriate) |
| 409 | `CONFLICT` / `SKU_TAKEN` / `EMAIL_TAKEN` / `INSUFFICIENT_STOCK` / `INVALID_STATE` | uniqueness/state/stock issues |
| 429 | `RATE_LIMITED` | login rate limit exceeded (retry-after headers) |
| 500 | `INTERNAL_ERROR` | unexpected; message generic, stack not leaked |
| 204 | — | successful deletion |

`requestId` is attached to every request (`x-request-id` header) and echoed in error bodies and logs.

## Testing

```bash
npm test              # all tests (unit + integration, runInBand)
npm run test:unit     # mocked/unit tests only
npm run test:integration  # real SQLite migrations + supertest
npm run test:coverage # coverage report
```

**Integration strategy:** global setup recreates the test DB from migrations (`prisma migrate deploy`), `configureSqlite()` applies PRAGMAs, each test gets a clean schema via `resetDatabase()`. Services are tested with real repositories against SQLite where concurrency/inventory behavior matters (checkout races, double-cancel).

**Key acceptance tests (to be satisfied):**
- Unauthorized access blocked (401/403)
- Failed checkout leaves inventory unchanged
- Concurrent purchases cannot oversell stock (e.g. stock 5, 10 parallel → exactly 5 succeed, 5 `INSUFFICIENT_STOCK`/`CONFLICT`, final stock 0)
- Cancellation cannot restore stock twice (second cancel → `INVALID_STATE`/409, stock restored exactly once)

## Docker

```bash
# Build and run API with a named volume for SQLite
cp .env.example .env   # fill JWT_SECRET
docker compose up --build

# Run the test suite inside the container
docker compose --profile test run --rm test

# Stop
docker compose down
```

Dockerfile is multi-stage (`node:24-alpine`), runs `prisma migrate deploy` before starting, uses a non-root user, and has a healthcheck hitting `/api/v1/health/ready`. SQLite file persists in `api-data:/app/data`.

## Design decisions

| Decision | Rationale |
|tag|Rationale|
|---|---|
| **Integer cents** | Avoid floating point for money; totals computed server-side. |
| **Prisma 6 (not 7)** | Stable generator, `.env` auto-load, no driver-adapter churn; easier to reason about. |
| **Atomic stock decrement** | `UPDATE Product SET stock = stock - qty WHERE id = ? AND stock >= qty` with affected-row count (no read-modify-write). Checkout wraps all lines + order creation + cart clear in `prisma.$transaction`. |
| **Exactly-once restock** | On cancel, `updateMany({ where: { id, status: in: eligible, stockRestoredAt: null }, data: { status: CANCELLED, stockRestoredAt: now() } })` is the first step — only one caller flips it; second gets 409 `INVALID_STATE`. `StockMovement` logs the delta. |
| **Order item snapshots** | History immune to catalogue edits; soft delete (`active=false`) preserves referential integrity. |
| **Ownership by userId from JWT** | Never trust client-supplied `userId`; cross-user access returns 404/403 as appropriate. |
| **Zod everywhere** | Validation, normalization, and (Stage 5) OpenAPI source of truth. |
| **Centralized errors** | Services throw `AppError`; one handler maps to envelope with `requestId`; no stack leak. |
| **SQLite pragmas** | WAL + busy timeout mitigate single-writer contention; schema Postgres-portable. |
| **Test DB from migrations** | Proves migrations are valid and suites are isolated. |

## Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | tsx watch |
| `npm run build` | `prisma generate && tsc -p tsconfig.build.json` |
| `npm start` | run built app |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint |
| `npm run format` | Prettier |
| `npm test` | Jest (all) |
| `npm run prisma:generate` | generate client |
| `npm run prisma:migrate` | dev migration |
| `npm run prisma:migrate:deploy` | apply migrations |
| `npm run prisma:seed` | seed data |
| `npm run openapi` | generate `docs/openapi.json` (Stage 5) |

## License

MIT
