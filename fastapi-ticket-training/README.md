# FastAPI Ticket Training Project

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+. Uses an in-memory store so no database setup is required.

## Setup

```bash
uv sync
uv run pytest -q
uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Dependency management

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.
`uv sync` installs them into `.venv`, and `uv run <cmd>` runs a command
in that environment (auto-syncing first).

```bash
uv add <package>          # runtime dependency
uv add --dev <package>    # test/tooling dependency
uv sync                   # install locked dependencies
```

## Training order

Ticket details live in [tickets/backlog.md](tickets/backlog.md).

1. Analyze RENT-201 through RENT-205 before looking at the implementation.
2. Start the app and reproduce RENT-206.
3. Record exact requests, responses, and observed/expected results.
4. Ask Claude for hypotheses; verify each against the code and tests.
5. Write a failing test before changing the implementation.
6. Fix the bug and run the full test suite.

The starter intentionally contains defects. The tests are expected to fail initially.
Data is reset whenever the app process restarts. This is a training fixture, not production storage.
