# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run pytest -q                       # run full test suite
uv run pytest tests/test_tickets.py::test_rent_201_balance_uses_only_payments_for_that_bill -v  # single test
uv run uvicorn app.main:app --reload   # dev server at http://127.0.0.1:8000
uv sync                                # install dependencies from uv.lock
```

No linter or formatter is configured. No database — the app uses an in-memory store that resets on restart.

## Architecture

This is a FastAPI billing API for room rentals. Amounts are in VND (integers, no decimals).

- `app/main.py` — route definitions only; delegates to service functions
- `app/service.py` — all business logic (bill lookups, payment creation, overdue calculation)
- `app/store.py` — in-memory fixtures (`bills` dict, `payments` list, `idempotency_keys` dict); module-level state shared across requests
- `app/schemas.py` — Pydantic request/response models
- `tests/conftest.py` — `reset_store` fixture (autouse) resets `store` state before each test
- `tickets/` — training ticket descriptions and analysis templates

The store is intentionally seeded with defects. Tests in `test_tickets.py` are named after ticket IDs (RENT-201 through RENT-206) and are expected to fail until the corresponding bugs are fixed.

## Testing

Tests use `fastapi.testclient.TestClient` (backed by `httpx`). The `reset_store` fixture in `conftest.py` restores seed data before every test — new tests do not need to manage store state manually.
