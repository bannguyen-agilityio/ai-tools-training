# CLAUDE.md

LeaveDesk: internal leave tool for ~250 staff (16 managers, 2 HR), replacing Excel + email. The spec is the source of truth. Built so far: backend core, audit, identity, balance ledger + `compute_balance` + rollover/expire_carry jobs (`GET /me/balances` + `ensure_sufficient` for the R10 check, Dashboard balance cards), HR balances API (#23–#26: manual entries, preview, ledger, launch list), email outbox + `EmailSender`, notifications API, `drain_outbox` job, frontend shell (R31 primitives in `frontend/src/ui`, served by `app/spa.py`; see `frontend/README.md`), public holidays (seeded, HR CRUD, impact count), working-day expansion (`leave_days/calendar.py`) and the `leave_request`/`leave_request_day` tables (`days_for` reads them), request create/preview/list/detail (`POST /requests`, `POST /requests/preview`, `GET /me/requests`, `GET /requests/{id}`) with overlap, past-date and routing rules, HR Holidays and Balances screens, New request / My requests / Request detail screens, approve/reject (`GET /approvals?scope=assigned`, `POST /approvals/{id}/approve|reject`, `can_decide`, Approvals screen). Owner cancel of a Pending request (`POST /requests/{id}/cancel`, R16). Deactivation (`POST /hr/employees/{id}/deactivate`, R4). Deputy HR admin (`GET/PUT /hr/deputy`, HR admin leave routes to the deputy, R36, HR Settings). Cover for an absent manager (`scope=cover`, `on_behalf_of`, audit `acting_for_id`, direct manager emailed, "On behalf of" tab, R20). Not built: HR cancel, notification bell UI, other feature screens.

## Sources

- `specs/001-leave-management-tool/`: `intent.md` (scope, constraints), `spec.md` (R1–R36, data model §5, API §6, screens §7, privacy §8, concerns C-1–C-18, decisions §13), `plans/` (per R-number), `mocks/`. Read the relevant section before building; cite R#/C-# in commits and PRs.
- `docs/runbooks/` (deploy, secrets); `.env.example` lists every variable.
- **Do not read `ref/`** (stale training material). Never open, search or cite it.
- If code and spec disagree, fix the spec in the same change. Non-intent items are marked **[Assumption]**.
- Known drift: spec §2 says Python 3.12; it is 3.14.

## Phases

- **P1 (1 Nov 2026):** auth, requests, approvals, HR admin, balances, holidays, audit, email + in-app notifications, HR "All leave" list.
- **P2 (16 Nov 2026):** team calendar (R27), monthly report (R28).
- Never cut authorization, audit or tests to hit the date.
- Out of scope: Google SSO (first post-launch), Slack/Teams, history/balance CSV import, other leave types, non-Vietnamese holidays, Saturday/shift patterns.

## Stack and commands

- Backend: Python 3.14, FastAPI, async SQLAlchemy 2 (psycopg), Alembic, `uv`. Vertical modules in `app/modules/<name>/` (router, service, repository, models, schemas, dependencies); shared code in `app/core/`. Use the `add-endpoint` skill. Routers use prefix `/api/v1/...` and are included in `create_app()`.
- DB: Supabase Postgres as hosted Postgres only (no Supabase Auth/REST). RLS on with **no policies** on every table; a test must prove the anon key reads nothing. Migrations run as owner; the app runs as `APP_DB_ROLE` (no UPDATE/DELETE on append-only tables). Alembic keeps a single head.
- Frontend: React 18, TypeScript, Vite, React Router, TanStack Query, React Hook Form + Zod. Served by FastAPI at `/`, API at `/api/v1`, same origin.
- Auth: email + password (Argon2id via `argon2-cffi`, `secrets`, no custom crypto). Hashed session token in an `HttpOnly; Secure; SameSite=Lax` cookie; `X-CSRF-Token` + `Origin` check on state-changing calls. `user_identity` keeps provider separate for SSO.
- Email: SendGrid behind `EmailSender`; `EMAIL_BACKEND=mock` dev/tests only (app refuses it in production). Outbox with retry.
- Hosting: FastAPI Cloud, ≤ $5/month; build gated on hello-world deploy + cost check (C-16, Q5). Config is env-only (`pydantic-settings`); secrets never committed. `/docs` only when `ENVIRONMENT=dev`.
- Jobs: idempotent `python -m app.jobs.<name>` from scheduled CI.

```bash
uv sync && uv run alembic upgrade head
uv run fastapi dev
uv run pytest        # needs TEST_DATABASE_URL (owner Postgres; docs/runbooks/secrets.md §4)
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pyright
uv run python scripts/check_single_head.py
```

Frontend checks: Vitest, React Testing Library, eslint, `tsc --noEmit`; Playwright against staging. Tests mirror the source tree under `tests/`.

## Business rules

- Leave year Jan–Dec in `COMPANY_TZ` (`Asia/Ho_Chi_Minh`); "today", notice, year boundary and holidays use it.
- Annual 12 days/yr; carry-over max 6 unused, expires 31 Dec of the next year, never re-carried, consumed first. Sick 7 paid days, no carry-over, entered up to 7 days back (older: HR only). Unpaid: no balance.
- Working days = Mon–Fri minus Vietnamese public holidays (HR-editable). Half day = 0.5. Requests spanning two years deduct per year.
- Pending requests reserve days: Available = entitlement + carried − used − reserved.
- Notice: single-day Annual/Unpaid needs 1 day (hard block); >5 working days needs 1 week (warning). Sick exempt.
- Routing: employee → manager; manager → HR; HR → deputy. Never approve your own. Rejection needs a 1–500 char reason. Cover for an absent manager only via "On behalf of", audited, direct manager emailed.
- Cancel: employee while Pending; only HR once Approved (refund exactly once).
- New joiners pro-rated by remaining months (start day 1–15 counts that month), Annual and Sick, nearest 0.5.
- Holiday edits never rewrite `working_days`; HR sees impacted requests and adjusts via ledger.

## Architecture rules

- Balances are **derived**: one pure `compute_balance(entries, days, today)` holds all balance rules.
- `balance_entry` and `audit_log` are append-only; corrections are new adjustment entries with a reason.
- `leave_request_day`: one row per working half day; partial unique index `(employee_id, leave_date, slot) WHERE is_active` prevents overlap.
- `approve`/`reject`/`cancel` carry `version`; stale → `409`. Submit locks the employee row (`FOR UPDATE`).
- Authorize in the service layer on every request. Every endpoint needs a 401/403 test per role.
- Strict request schemas (`StrictModel`, unknown fields refused); parameterised queries only.
- Errors: `{ "error": { code, message, details[] } }` (spec §6.1); `error.stack` only when `ENVIRONMENT` is not `production`.
- Quantities `numeric(4,1)` in 0.5 steps; uuid ids; `timestamptz` UTC.

## Privacy (non-negotiable)

- Redact on the **server**. Sick type is visible only to the owner, the deciding/covering approver while deciding, and HR; everyone else sees "Off", identical for Pending and Approved.
- Emails, notifications, audit/app logs and exports never contain Sick type, notes, rejection reasons (except to the employee), passwords or tokens.
- Report/export: HR-only, audited, formula-escaped (`= + - @ tab`), marked confidential.
- Managers cannot see their reports' balances.

## Conventions

- Write auth, authorization and balance tests first. Run `security-review` on auth before go-live.
- Dates unambiguous ("Mon 2 Nov 2026"). UI passes R31: 360 px, 44 px targets, WCAG 2.1 AA, labelled fields, focus on first error, destructive confirms default to "Keep".
- Implementing a task, issue or plan ("implement leavedesk-NN-rNN", "#40"): invoke the `implement-task` skill first, before reading code or writing any. It drives the board, branch, tests, review and PR. Delegate large independent chunks to sub-agents when asked.
- Before creating a PR, run all three review skills on the working-tree diff: `review-checklist`, `code-review` (at `medium`; `max` and `ultra` only when asked) and `security-review`. All three are required for every PR, not only auth changes. Fix confirmed correctness, security and privacy findings and rerun the affected checks. List every finding with its outcome (fixed, not fixed with reason, false positive) in the PR "Review" section. Do not open the PR until all three have run; if one cannot run, say so in the PR instead of skipping it silently.
- New or changed env var (any `Settings` field): update every place in the same change. `.env.example`, `docs/runbooks/secrets.md`, `tests/test.env`, and the workflows under `../.github/workflows/leavedesk-*.yml`: `leavedesk-ci`, `leavedesk-deploy-env` (the migrate step loads `get_settings()` too, so it needs every required setting), and each `leavedesk-job-*` (jobs load full settings). Scope secrets to the step that needs them. Jobs and deploys read secrets from GitHub environments (`staging`, `production`), never repo-level. Grep the variable name across all of these before opening the PR.
- Git: branch off `main`; conventional commits (`docs:`, `feat:`, `refactor:`).
