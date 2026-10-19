# CLAUDE.md

## Commands

```bash
uv sync --all-groups            # Install all dependencies
uv run uvicorn app.main:app --reload  # Dev server (auto-reloads)
uv run pytest                   # Run tests
uv run ruff check .             # Lint
uv run ruff check . --fix       # Auto-fix lint issues
uv run ruff format .            # Format code
uv run pyright                  # Type check

# Run all quality checks (run after every change)
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest
```

## Environment

Copy `.env.sample` to `.env`. All variables use the `APP_` prefix (see `app/core/config.py`).
The database is async SQLite via SQLAlchemy + aiosqlite. Tables are auto-created on startup—no migration tool.

## Architecture

Feature modules live under `app/modules/<feature>/` with this layering:

| Layer | Responsibility | Why |
|---|---|---|
| **Router** | HTTP handling, status codes, DI wiring | Keeps transport concerns out of business logic |
| **Service** | Business rules, raises domain exceptions | Testable without HTTP or DB |
| **Repository** | Data access via `AsyncSession` | Isolates query details; services only see the interface |
| **Models** | SQLAlchemy ORM entities | Single source of truth for table shape |
| **Schemas** | Pydantic request/response models | Decouples API shape from DB shape |

Shared code: `app/core/` (config, exceptions, error schemas, security). Infrastructure: `app/infrastructure/` (engine, session factory, `Base`).

Routes are registered centrally in `app/api/v1/router.py` under the `/api/v1` prefix—never scattered across modules. This keeps versioning in one place and makes it possible to add `/api/v2` without hunting for hardcoded prefixes.

## Authentication

Stateless JWT auth via `OAuth2PasswordBearer` (tokenUrl: `/api/v1/auth/login`). Tokens are signed with `APP_SECRET_KEY` (HS256, configurable expiry via `APP_ACCESS_TOKEN_EXPIRE_MINUTES`). The `get_current_user` dependency extracts the `Authorization: Bearer <token>` header, decodes the JWT, and returns the username — no token storage. Passwords are hashed with PBKDF2-SHA256 + per-user salt (`app/core/security.py`).

## Error Handling

All errors use the envelope defined in `app/core/schemas.py`:

```json
{"error": {"code": "UPPER_SNAKE_CODE", "message": "...", "details": null, "request_id": "..."}}
```

- Services raise domain exceptions from `app/core/exceptions.py` (e.g., `AuthenticationError`, `ConflictError`). They never return HTTP responses.
- `app/core/error_handlers.py` converts those exceptions into the envelope. Validation errors (422) include per-field `details`.
- New error types: subclass `AppError`, pick a stable code and appropriate status. The handler picks it up automatically.

## Conventions

- **Docstrings:** Google-style, enforced by Ruff `D` rules. Every module, public class, and public function needs one. Keep them short—don't repeat what type hints already say.
- **Async:** Use `async def` for any I/O operation. The DB session, engine, and all repository methods are async.
- **Transactions:** The session's request-scoped `get_db_session` generator commits on success and rolls back on error. Repositories call `flush()`, not `commit()`.
- **Tests:** pytest + pytest-asyncio (`asyncio_mode = "auto"`). Use FastAPI `TestClient` for endpoint tests; test services directly for business logic.

## Never Do

- Put business logic or SQL in routers. *Routers only wire things together.*
- Let services import FastAPI, `Request`, or concrete DB types. *Breaks testability and the dependency rule.*
- Return HTTP responses from services or repositories. *Raise an `AppError` subclass; let the handler convert it.*
- Expose stack traces, SQL, or internal paths in error responses. *Security risk; log them server-side instead.*
- Hardcode secrets or skip auth to make tests pass. *Use `.env` and dependency overrides.*
- Introduce breaking changes to `/api/v1` without approval. *Clients depend on stable codes and shapes.*
