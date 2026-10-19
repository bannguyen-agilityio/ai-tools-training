# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
cp .env.sample .env           # Then edit — at minimum set APP_SECRET_KEY and APP_SEED_PASSWORD
uv sync --all-groups          # Install all dependencies (including dev)
```

## Build & Run Commands

```bash
uv run uvicorn app.main:app --reload   # Dev server at http://localhost:8000
uv run pytest                 # Run all tests
uv run pytest app/tests/modules/auth/test_service.py  # Single test file
uv run pytest -k test_login   # Single test by name
uv run ruff check .           # Lint
uv run ruff format .          # Format
uv run pyright                # Type check
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest  # All checks
```

## Architecture

FastAPI app with async SQLAlchemy (aiosqlite), structured as vertical modules under `app/modules/`. Each module follows the same layered pattern:

- **router.py** — HTTP endpoints, delegates to the service layer
- **service.py** — Business logic, raises domain exceptions from `app.core.exceptions`
- **repository.py** — Data access via async SQLAlchemy session
- **models.py** — SQLAlchemy ORM models inheriting `app.infrastructure.database.Base`
- **schemas.py** — Pydantic request/response models
- **dependencies.py** — FastAPI dependency injection wiring (repository → service → router)

Modules: `auth` (user registration, JWT login, token resolution) and `todo` (CRUD, scoped to the authenticated user).

### Key conventions

- All API routes are versioned under `/api/v1` via `app.api.v1.router`
- Domain errors extend `AppError` (`app.core.exceptions`) and are converted to a standard JSON error envelope `{"error": {"code", "message", "details", "request_id"}}` by handlers in `app.core.error_handlers`
- A request-ID middleware (`req_<hex>`) is attached to every request
- Auth uses PBKDF2-SHA256 password hashing with per-user salts, and HS256 JWT tokens
- The `todo` module resolves the current user's DB ID via `get_current_user_id` dependency, which chains through the auth module's `get_current_user` (bearer token → username)
- Pagination uses `PaginationParams` / `PaginatedResponse[T]` from `app.core.pagination`
- Settings load from `APP_`-prefixed env vars via pydantic-settings (`app.core.config`)
- Database tables are auto-created on startup in the lifespan handler; a seed user is inserted from env vars
- Tests use an in-memory SQLite database with `StaticPool`; the `conftest.py` overrides `get_db_session` and provides `client`, `auth_token`, `auth_headers`, and `db_session` fixtures. The `conftest.py` sets `APP_*` env vars via `os.environ.setdefault` **before** importing any app modules — new test helpers must preserve this ordering
- `asyncio_mode = "auto"` in `pyproject.toml` — async test functions run without explicit `@pytest.mark.asyncio`
- Python 3.14+, ruff lint uses Google-style docstrings (`extend-select = ["D"]`)
