# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Mini e-commerce REST API: Express 5, TypeScript (strict), Prisma 6 + SQLite, Zod 4, Jest 30 + Supertest. Served under `/api/v1`. Requires Node >= 20.11.

## Commands

```bash
cp .env.example .env && npm ci
npx prisma generate && npx prisma migrate dev   # create/update prisma/dev.db
npm run prisma:seed                             # admin@shop.local / customer@shop.local, Password123!
npm run dev                                     # tsx watch, http://127.0.0.1:3000/api/v1 (Swagger at /api/v1/docs)

npm run typecheck
npm run lint                                    # eslint (lint:fix to autofix)
npm run format:check                            # prettier (format to write)
npm run build                                   # prisma generate + tsc -p tsconfig.build.json -> dist/

npm test                                        # unit + integration, --runInBand
npm run test:unit
npm run test:integration
npx jest --selectProjects unit -t "name"        # single test by name
npx jest tests/integration/health.test.ts       # single file
npm run openapi                                 # regenerate docs/openapi.json
```

## Architecture

- `createApp()` in `src/app.ts` is a factory (no listen); `src/server.ts` does bootstrap and graceful shutdown. Tests import `createApp()` with Supertest.
- Middleware order matters: helmet → cors → body parsers → `requestContext` (assigns `requestId`) → pino-http (reuses that id) → docs → routers → `notFoundHandler` → `errorHandler`.
- Layering rule: `route → controller (HTTP only) → service (business rules) → repository (Prisma)`, organized as vertical modules in `src/modules/<name>/`. Services throw `AppError` subclasses (`src/core/errors.ts`); the central `src/core/error-handler.ts` maps `AppError`, Zod, Prisma and JSON-parse errors into the standard envelope (`src/core/response.ts`). Repositories never build HTTP responses.
- Only the `health` module is implemented so far. README describes the planned auth/users/products/cart/orders modules, `middleware/auth|validate|rate-limit`, and `utils/`, which do not exist yet. Check `src/` before assuming something is there.
- Config: `src/config/env.ts` validates env with Zod (fail fast); `src/config/prisma.ts` is the singleton client and applies SQLite PRAGMAs (WAL, busy_timeout, foreign_keys). `DATABASE_URL` must keep `connection_limit=1` (single writer).
- Domain invariants (from schema/README design): money is integer cents (`priceCents`); order items snapshot price/SKU/name; stock is decremented by conditional `UPDATE ... WHERE stock >= qty` inside one `$transaction` at checkout; stock restoration on cancel is exactly-once via a `stockRestoredAt` compare-and-swap; `StockMovement` is an append-only ledger. Products are soft-deleted via `active`.
- OpenAPI: `src/docs/openapi.ts` is a hand-written `OpenAPIV3.Document` (exported via `buildOpenApiDocument`), served by `src/docs/swagger.ts`. `docs/openapi.json` is generated, so rerun `npm run openapi` after changing the spec. Add new endpoints to the spec too.

## Testing

- Jest has two projects (`jest.config.js`): `unit` (`tests/unit`) and `integration` (`tests/integration`).
- Integration global setup (`tests/setup/global.ts`) deletes `prisma/test.db*` and runs `prisma migrate deploy` against `TEST_DATABASE_URL`. Schema changes therefore need a checked-in migration (`npm run prisma:migrate`), not just `db push`.
- `tests/helpers/database.ts` `resetDatabase()` wipes tables children-first before each integration test. Add any new Prisma model to it, in FK-safe order.
- Integration tests must run serially (`--runInBand`) because SQLite has a single writer.
