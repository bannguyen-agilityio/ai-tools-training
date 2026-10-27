# AI Support Agent Evals

A runnable starter project demonstrating deterministic tests and continuous evaluations in CI.

## Requirements
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `jq` (only needed for the shell-based JSON checker)
- Git (recommended)

## Quick start

```bash
uv sync
uv run pytest -q
uv run ruff check src tests
uv run bash evals/check.sh evals/refund-policy.json
```

The project is deliberately self-contained: it uses a local support-policy implementation so you can run the tests without an LLM API key.

## What it demonstrates
- Explicit, deterministic support-policy behavior.
- Logging that avoids recording message text or full responses.
- JSON-defined evaluation checks.
- A GitHub Actions workflow that runs tests on pull requests and on a schedule.

## Optional: add Claude Code to the loop
This starter does **not** launch Claude Code automatically. That should be a deliberate next step with restricted permissions and a separate trusted evaluator. Before enabling an agent job:
1. Store the API credential in GitHub Actions Secrets.
2. Run the agent in an isolated checkout or disposable environment.
3. Restrict tools, network access, and writable paths.
4. Keep evaluator scripts and expected results outside the agent's writable scope.
5. Require human review for sensitive or production-impacting changes.

## Project structure

```text
ai-support-agent-evals/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── uv.lock
├── src/
│   └── support.py
├── tests/
│   └── test_support.py
├── evals/
│   ├── refund-policy.json
│   ├── no-sensitive-logs.json
│   └── check.sh
└── .github/
    └── workflows/
        └── agent-evals.yml
```

## Evaluation limitations
The shell checker runs commands declared in JSON. Treat evaluation files as trusted repository code: never execute untrusted commands from user-supplied JSON. The included checks are deterministic; they do not establish that an LLM's free-form response is semantically correct. Extend with rubric-based or model-graded evaluations for an actual AI agent.
