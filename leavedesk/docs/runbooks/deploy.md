# Deploy and rollback

## Flow (`.github/workflows/leavedesk-deploy.yml`)

The environment is inferred from the branch:

| Branch | Environment | Gate |
|---|---|---|
| `staging` | staging | none (automatic) |
| `main` | production | required reviewers on the `production` GitHub environment |

Any other branch fails at the `target` job. Promote by merging `staging` into `main`.

Steps for the chosen environment:

1. CI checks (ruff, mypy, single Alembic head, pytest, migration cycle).
2. Build the frontend (`npm ci && npm run build` in `leavedesk/frontend`; a failed build stops the run), single-head check, `alembic upgrade head` as the owner (a failed migration stops the run before any deploy), `fastapi deploy`, then `/healthz` must return `{"status":"ok"}` and `/` must return the SPA shell.
3. Production only: `tag-production` tags the commit `prod-<UTC timestamp>-<sha>`.

Deploys per environment never run in parallel and are never cancelled mid-run.

## One-time setup

Create the two FastAPI Cloud apps and databases, create the `staging` branch, create the two GitHub environments, and fill in everything listed in `secrets.md`. Not yet done: this needs the Q5 hello-world result (cost, pooled DB, scheduled CI).

## Manual run

Actions > leavedesk-deploy > Run workflow. On a branch, the environment is inferred as above. On a tag, set `environment`.

## Rollback

1. Pick the last good tag: `git tag --list 'prod-*' --sort=-creatordate`.
2. Run the workflow on that tag (or set `ref` to it) with `environment` = `production`. It re-checks, then waits for approval.
3. Migrations are not reversed. Prefer a forward-fix migration; run a down-migration only if it was tested. `alembic upgrade head` on an older tag is a no-op when the database is already ahead, so older code must tolerate the newer schema.

Rehearse this on staging (`environment` = `staging`) before go-live.
