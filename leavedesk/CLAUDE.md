# CLAUDE.md

LeaveDesk: internal leave management tool for ~250 staff (16 managers, 2 HR). Replaces Excel + email requests. No application code exists yet; the spec is the source of truth.

## Source documents

- `specs/001-leave-management-tool/intent.md`: problem, scope, constraints.
- `specs/001-leave-management-tool/spec.md`: requirements (R1–R36), data model (§5), API (§6), screens (§7), privacy matrix (§8), concerns (C-1–C-18), decisions log (§13). Read the relevant section before building; cite R#/C-# in commits and PRs.
- `specs/001-leave-management-tool/mocks/`: UI mocks.
- **Do not read `ref/`.** It is training material only and contains stale figures. Never open, search or cite files under it; the intent and spec are the only sources.
- If code and spec disagree, fix the spec in the same change. Anything not in the intent is marked **[Assumption]** in the spec.

## Phases

- **P1 (go-live 1 Nov 2026):** auth, requests, approvals, HR admin, balances, holidays, audit, email + in-app notifications, HR "All leave" list.
- **P2 (Mon 16 Nov 2026):** team calendar (R27) and monthly report (R28).
- Never cut authorization, audit or tests to hit the date.
- Out of scope: Google SSO (first post-launch item), Slack/Teams, history import, balance CSV import, other leave types, non-Vietnamese holidays, Saturday/shift patterns.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, vertical modules (router, service, repository, models, schemas, dependencies). Use the `add-endpoint` skill for new endpoints.
- DB: PostgreSQL on Supabase (free tier, Singapore) as hosted Postgres only. Not Supabase Auth or its REST/GraphQL. RLS enabled with **no policies** on every table; a test must prove the anon key reads nothing.
- Frontend: React 18 + TypeScript + Vite, React Router, TanStack Query, React Hook Form + Zod, mobile-first CSS. Build output served by FastAPI at `/`; API at `/api/v1`, same origin (no CORS).
- Auth: in-app email + password (Argon2id via `argon2-cffi`, tokens via `secrets`, no custom crypto). Hashed session token in an `HttpOnly; Secure; SameSite=Lax` cookie, `X-CSRF-Token` header + `Origin` check on state-changing calls. `user_identity` table keeps provider separate for future SSO.
- Email: SendGrid behind an `EmailSender` interface; `EMAIL_BACKEND=mock` for dev/tests only (app refuses to start with mock in production). Outbox pattern with retry.
- Hosting: FastAPI Cloud (one service, `fastapi deploy`), budget ≤ $5/month. Build is gated on the hello-world deploy + cost check (C-16, Q5).
- Jobs: CLI commands `python -m app.jobs.<name>` run from scheduled CI; all idempotent.
- Tests/lint: pytest, httpx, ruff, mypy; Vitest, React Testing Library, eslint, `tsc --noEmit`; Playwright against staging.

## Business rules to get right

- Leave year Jan–Dec in `COMPANY_TZ` (`Asia/Ho_Chi_Minh`). "Today", notice, year boundary and holidays all use it.
- Annual 12 days/yr; carry-over max 6 of the current year's unused days, expires 31 Dec of the following year, never re-carried, consumed first. Sick 7 paid days, no carry-over, may be entered up to 7 days back (older: HR only). Unpaid: unlimited, no balance.
- Working days = Mon–Fri minus Vietnamese public holidays (HR-editable). Half days count 0.5. A request spanning two years deducts per year.
- Pending requests reserve days: Available = entitlement + carried − used − reserved.
- Notice: single-day Annual/Unpaid needs 1 day (hard block). More than 5 working days: 1 week, warning only. Sick exempt.
- Routing: employee → direct manager; manager → HR; HR → deputy. Nobody approves their own request. Rejection needs a 1–500 char reason. Cover-for-absent-manager only via the "On behalf of" tab, audited, direct manager emailed.
- Cancel: employee while Pending; only HR once Approved (refund exactly once).
- New joiners pro-rated by remaining months (start on day 1–15 counts that month), Annual and Sick, nearest 0.5 day.
- Holiday edits never rewrite `working_days`; HR sees impacted requests and adjusts via ledger.

## Architecture rules

- Balances are **derived**, never stored: one pure function `compute_balance(entries, days, today)` holds all balance rules.
- `balance_entry` and `audit_log` are append-only (no UPDATE/DELETE for the app role). Corrections are new adjustment entries with a reason.
- `leave_request_day` stores one row per working half day; a partial unique index on `(employee_id, leave_date, slot) WHERE is_active` prevents overlap under concurrency.
- Optimistic locking: `approve`/`reject`/`cancel` carry `version`; stale → `409`. Submit locks the employee row (`FOR UPDATE`).
- Authorization is checked in the service layer on every request; hiding a button is not access control. Every endpoint needs a 401/403 test per role.
- All request bodies use strict schemas (unknown fields refused); parameterised queries only; errors are RFC 9457 `problem+json` with no stack traces.
- Day quantities are `numeric(4,1)` in 0.5 steps; ids are uuid; timestamps `timestamptz` UTC.

## Privacy rules (non-negotiable)

- Redact on the **server**, not in the UI. Sick leave type is visible only to the owner, the deciding/covering approver while deciding, and HR. Everyone else sees "Off", identical for Pending and Approved.
- Emails, in-app notifications, audit/app logs and exports never contain the Sick type, notes, rejection reasons (except to the employee), passwords or tokens.
- Report/export: HR-only, audited, formula-escaped (`= + - @ tab`), marked confidential.
- Managers cannot see their reports' balances.

## Conventions

- Auth, authorization and balance tests are written first. Run `security-review` on the auth module before go-live.
- Dates shown unambiguously (e.g. "Mon 2 Nov 2026"). UI must pass R31: 360 px wide, 44 px touch targets, WCAG 2.1 AA, labelled fields, focus on first error, destructive actions confirm with default focus on "Keep".
- Secrets live in platform environment variables, never committed.
- Git: branch off `main`; commit messages in conventional style (`docs:`, `feat:`, `refactor:`).
