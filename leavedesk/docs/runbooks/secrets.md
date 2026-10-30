# Configuration, variables and secrets

Everything is configured through environment variables (or the `.env` file locally). There are no deployment defaults in code: a missing required value stops the app at startup. Names only here; never commit values. The single owner who can rotate secrets is the developer (Q13).

Where each kind of value lives:

| Place | Read by | Used for |
|---|---|---|
| GitHub environments `staging`, `production` | `leavedesk-deploy*.yml` | deploy token, migrations, health check |
| FastAPI Cloud app environment (one per app) | the running app | runtime settings and secrets |
| `.env` (git-ignored) | local dev | copy from `.env.example` |
| `tests/test.env` + `TEST_DATABASE_URL` | pytest | tests; no real secrets |

## 1. GitHub environments

Settings > Environments. Create `staging` and `production`, each with its own values.

### Secrets (per environment)

| Name | Value |
|---|---|
| `FASTAPI_CLOUD_TOKEN` | FastAPI Cloud API token used by `fastapi deploy` |
| `SENDGRID_API_KEY` | SendGrid key, read by the `drain_outbox` job (each environment) |
| `DATABASE_URL` | App database URL: `postgresql+psycopg://<app_role>:<password>@<pooled-host>:<port>/<db>` |
| `MIGRATION_DATABASE_URL` | Owner/admin URL of the same database, used only by `alembic upgrade head` |

### Variables (per environment)

| Name | Value |
|---|---|
| `FASTAPI_CLOUD_APP_ID` | ID of that environment's FastAPI Cloud app |
| `APP_URL` | Base URL of that app, no trailing slash (used for the `/healthz` check) |
| `APP_DB_ROLE` | Role the app runs as, e.g. `leavedesk_app` |
| `COMPANY_TZ` | `Asia/Ho_Chi_Minh` |
| `EMAIL_FROM` | Verified SendGrid sender, read by the `drain_outbox` job |

Scheduled jobs (`leavedesk-job-*`; schedules are disabled for now, manual runs only) run once per environment (staging and production; manual runs follow the branch) and read `DATABASE_URL`, `APP_DB_ROLE`, `COMPANY_TZ`, `APP_URL` (as `APP_BASE_URL`) and, for `drain_outbox`, the two email values above.

### Protection rules

- `production`: add **required reviewers**. Their approval is the production gate (A-27).
- Restrict deployment branches: `staging` environment from branch `staging` only, `production` from `main` only. This matches the branch-to-environment mapping in `deploy.md`.
- Keep production secrets on the `production` environment only, never as repository secrets.

### Set by the workflow (do not configure)

`ENVIRONMENT` (from the environment name), `APP_BASE_URL` (from `APP_URL`), `EMAIL_BACKEND=sendgrid`, `COOKIE_SECURE=true`, `ENV_FILE=/dev/null`. `leavedesk-ci` needs nothing: its throwaway Postgres credentials are in the workflow file.

## 2. FastAPI Cloud app environment

Set in the dashboard or CLI for each app (staging and production). These are what the deployed app reads.

| Name | Required | Value |
|---|---|---|
| `ENVIRONMENT` | yes | `staging` or `production`; must match the GitHub environment (nothing checks this) |
| `DATABASE_URL` | yes | App-role URL of **that environment's own** database |
| `APP_DB_ROLE` | yes | Same as the GitHub variable |
| `COMPANY_TZ` | yes | `Asia/Ho_Chi_Minh` |
| `EMAIL_BACKEND` | yes | `sendgrid`. The app refuses `mock` when `ENVIRONMENT=production` |
| `COOKIE_SECURE` | yes | `true` (set `false` only for plain-HTTP local dev, A-25) |
| `APP_BASE_URL` | yes | Origin used for email links, no trailing slash (same as `APP_URL`) |
| `SENDGRID_API_KEY` | yes | SendGrid key (required with `EMAIL_BACKEND=sendgrid`) |
| `EMAIL_FROM` | yes | Verified sender address |
| `LOGIN_IP_LIMIT` | no | Failed sign-ins per IP in 15 min, default `30` (A-6) |
| `CLIENT_IP_HEADER` | no | Header the trusted proxy sets with the client IP (right-most entry used); leave unset if no proxy |
| `SET_ROLE_ON_CONNECT` | no | Leave unset (default `false`). Only for local/CI with an owner URL |
| `ALLOWED_ORIGINS` | no | JSON list of extra allowed origins, e.g. `["https://x.example"]`. Not needed for same-origin |
| `SESSION_IDLE_HOURS` | no | Default `8` (R2) |
| `SESSION_MAX_HOURS` | no | Default `24` (R2) |

Sessions use a random token stored hashed, so there is no signing key.

## 3. Local development

Copy `.env.example` to `.env`, fill in every required value. Use `ENV_FILE=<path>` to read a different file. Real environment variables override the file.

## 4. Tests

`tests/test.env` holds the non-secret test settings. The database URL comes from `TEST_DATABASE_URL` (an owner URL, e.g. the CI Postgres service) and is required. Locally, start a throwaway Postgres:

```
docker run --rm -d --name leavedesk-pg -e POSTGRES_PASSWORD=test -p 5434:5432 postgres:16
export TEST_DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5434/postgres
```

## 5. First-time database setup (each environment)

1. Run the first migration with `MIGRATION_DATABASE_URL`. It creates `APP_DB_ROLE` **without login**, enables RLS with no policies, and withholds UPDATE/DELETE/TRUNCATE on `audit_log`.
2. As the owner, give the role a password: `ALTER ROLE <APP_DB_ROLE> LOGIN PASSWORD '...'`. Use that role in `DATABASE_URL` (GitHub and FastAPI Cloud). Not automated because it needs a password.
3. The role is created with `BYPASSRLS` (there are no policies). Whether Supabase's `postgres` role may create such a role is unverified; if the migration fails here, adjust before go-live.

## Rules

- Staging has its own database and secrets and never holds production data.
- Never log, commit or paste secret values; the app's logs and audit records already scrub `password`, `token` and similar keys.
- Rotating `DATABASE_URL` or the role password: update the GitHub environment secret and the FastAPI Cloud variable together, then redeploy.
