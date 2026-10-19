# Simple TODO App

A FastAPI application built with clean architecture principles. Currently provides user authentication with plans to add task management.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management

## Getting Started

```bash
# Install dependencies
uv sync --all-groups

# Copy and configure environment variables
cp .env.sample .env
# Edit .env — at minimum set APP_SECRET_KEY, APP_DATABASE_URL, and APP_SEED_PASSWORD

# Run the development server
uv run uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`. On first startup, database tables are created automatically and a seed user is inserted from the configured environment variables.

## Environment Variables

All variables use the `APP_` prefix. See `.env.sample` for the full list.

| Variable | Required | Description |
|---|---|---|
| `APP_DATABASE_URL` | Yes | Async database URL (e.g. `sqlite+aiosqlite:///./app.db`) |
| `APP_SECRET_KEY` | Yes | Secret key for the application |
| `APP_SEED_USERNAME` | Yes | Username for the initial seed user (3-50 chars) |
| `APP_SEED_PASSWORD` | Yes | Password for the initial seed user (8+ chars) |
| `APP_SEED_FULL_NAME` | Yes | Display name for the seed user |
| `APP_APP_NAME` | No | Application title (default: `Simple TODO App`) |
| `APP_DEBUG` | No | Enable debug mode (default: `false`) |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime in minutes (default: `30`) |

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Create a new user account | No |
| `POST` | `/api/v1/auth/login` | Log in and receive an access token | No |
| `GET` | `/api/v1/auth/me` | Get the current user's profile | Bearer |

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass", "full_name": "Alice A"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "securepass"}'
```

### Get Current User

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Error Responses

All errors follow a standard envelope:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Incorrect username or password",
    "details": null,
    "request_id": "req_abc123def456"
  }
}
```

## Project Structure

```
app/
├── main.py                  # Application entry point and lifespan
├── api/v1/router.py         # Versioned API router
├── core/
│   ├── config.py            # Settings from environment variables
│   ├── exceptions.py        # Domain exception classes
│   ├── error_handlers.py    # Centralized error envelope handlers
│   ├── schemas.py           # Shared response schemas
│   └── security.py          # Password hashing and token generation
├── infrastructure/
│   └── database.py          # Async SQLAlchemy engine and session
├── modules/auth/
│   ├── router.py            # Auth HTTP endpoints
│   ├── service.py           # Auth business logic
│   ├── repository.py        # User data access
│   ├── models.py            # User SQLAlchemy model
│   ├── schemas.py           # Request/response schemas
│   └── dependencies.py      # Dependency injection
└── tests/                   # pytest test suite
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run pyright

# Run all quality checks
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest
```
