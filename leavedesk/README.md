# LeaveDesk

Internal leave management tool for about 250 staff (16 managers, 2 HR). It replaces the Excel sheet and email requests with one place to request, approve and track leave.

- **P1 (go-live 1 Nov 2026):** auth, requests, approvals, HR admin, balances, holidays, audit, email and in-app notifications, HR "All leave" list.
- **P2 (16 Nov 2026):** team calendar and monthly report.

## Documentation

The spec is the source of truth. If code and spec disagree, fix the spec in the same change.

| Document | Contents |
| --- | --- |
| [`specs/001-leave-management-tool/intent.md`](specs/001-leave-management-tool/intent.md) | Problem, scope, constraints |
| [`specs/001-leave-management-tool/spec.md`](specs/001-leave-management-tool/spec.md) | Requirements (R1–R36), data model, API, screens, privacy matrix, concerns, decisions |
| [`specs/001-leave-management-tool/plans/`](specs/001-leave-management-tool/plans/) | Implementation plans |
| [`specs/001-leave-management-tool/mocks/`](specs/001-leave-management-tool/mocks/) | UI mocks |
| [`docs/runbooks/`](docs/runbooks/) | Operational runbooks |
| [`CLAUDE.md`](CLAUDE.md) | Project rules for contributors and AI assistants |

## Stack

- **Backend:** Python 3.14, FastAPI, SQLAlchemy 2 (async), Alembic. Vertical modules under `app/modules/`.
- **Database:** PostgreSQL on Supabase, used as hosted Postgres only. RLS is enabled with no policies on every table.
- **Frontend (planned):** React 18, TypeScript, Vite. Built output is served by FastAPI at `/`; the API lives at `/api/v1` on the same origin.
- **Auth:** in-app email and password (Argon2id), HttpOnly session cookie, CSRF token and `Origin` check on state-changing calls.
- **Email:** SendGrid behind an `EmailSender` interface.
- **Hosting:** FastAPI Cloud.

## Getting started

Requirements: Python 3.14 (pinned in `.python-version`), [uv](https://docs.astral.sh/uv/) and Docker (for the test database).

```bash
uv sync                      # install dependencies into .venv
cp .env.example .env         # then fill in the values
uv run alembic upgrade head  # apply migrations
uv run fastapi dev           # run locally (entrypoint: app.main:app)
```

`.env.example` documents every variable. Real secrets live in platform environment variables and are never committed. `EMAIL_BACKEND=mock` is for dev and tests only; the app refuses to start with it in production.

## Development

Tests need an owner Postgres URL in `TEST_DATABASE_URL` (see `docs/runbooks/secrets.md`, section 4):

```bash
docker run --rm -d --name leavedesk-pg -e POSTGRES_PASSWORD=test -p 5434:5432 postgres:16
export TEST_DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5434/postgres

uv run pytest                          # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run python scripts/check_single_head.py   # Alembic must have a single head
```

Conventions:

- Write auth, authorization and balance tests first. Every endpoint needs a 401/403 test per role.
- Balances are derived (`compute_balance`), never stored. `balance_entry` and `audit_log` are append-only.
- Redact private data (such as the Sick leave type) on the server, not in the UI.
- Branch off `main`, use conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`) and cite R#/C-# from the spec in commits and PRs.

## Project layout

```
app/
  core/       config, db, errors, CSRF, security headers, logging
  modules/    vertical modules (audit, identity, ...)
migrations/   Alembic migrations
scripts/      repo tooling
tests/        pytest suite
specs/        intent, spec, plans, mocks
docs/         runbooks
```
