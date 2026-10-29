# Deploy and rollback

## Flow (`.github/workflows/leavedesk-deploy.yml`)

1. Push to `main` touching `leavedesk/**` runs the CI checks (ruff, mypy, single Alembic head, pytest, migration cycle).
2. `deploy-staging`: single-head check, `alembic upgrade head` as the owner, `fastapi deploy`, then `/healthz` must return `{"status":"ok"}`. A failed migration stops the run before any deploy.
3. `deploy-production`: same steps, but the `production` environment waits for a required reviewer.
4. `tag-production` tags the commit `prod-<UTC timestamp>-<sha>`.

Deploys per environment never run in parallel and are never cancelled mid-run.

## One-time setup

Create the two FastAPI Cloud apps and databases, the two GitHub environments, and fill in everything listed in `secrets.md`. Not yet done: this needs the Q5 hello-world result (cost, pooled DB, scheduled CI).

## Manual run

Actions > leavedesk-deploy > Run workflow. Leave `ref` empty to deploy the selected branch.

## Rollback

1. Pick the last good tag: `git tag --list 'prod-*' --sort=-creatordate`.
2. Actions > leavedesk-deploy > Run workflow, set `ref` to that tag. It re-checks, redeploys staging, then production after approval.
3. Migrations are not reversed. Prefer a forward-fix migration; run a down-migration only if it was tested. `alembic upgrade head` on an older tag is a no-op when the database is already ahead, so older code must tolerate the newer schema.

Rehearse this on staging before go-live.
