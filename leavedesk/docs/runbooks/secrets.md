# Secrets and deploy configuration inventory

Names only. Never commit values. Owner who can rotate: the developer (single owner, Q13).

## GitHub environments `staging` and `production`

Create both under Settings > Environments. On `production`, add **required reviewers**: that approval is the production gate (A-27). Keep the production secrets scoped to that environment only.

| Name | Kind | Purpose |
|---|---|---|
| `FASTAPI_CLOUD_TOKEN` | secret | CI token for `fastapi deploy` |
| `DATABASE_URL` | secret | Pooled async URL (`postgresql+psycopg://`), app role |
| `MIGRATION_DATABASE_URL` | secret | Owner URL used only by `alembic upgrade head` in CI |
| `FASTAPI_CLOUD_APP_ID` | variable | Which FastAPI Cloud app this environment deploys to |
| `APP_URL` | variable | Base URL for the `/healthz` check, no trailing slash |
| `APP_DB_ROLE` | variable | Role the app runs as; migrations grant it privileges |
| `COMPANY_TZ` | variable | `Asia/Ho_Chi_Minh` |

## FastAPI Cloud app environment (runtime, one set per app)

Set in the FastAPI Cloud dashboard or CLI for each app (staging, production). The deployed app reads these; the workflow's copies above are only for migrations.

`ENVIRONMENT`, `DATABASE_URL`, `APP_DB_ROLE`, `COMPANY_TZ`, `EMAIL_BACKEND` (`sendgrid`; the app refuses `mock` in production), `COOKIE_SECURE` (`true`), SendGrid API key, session signing key.

## Rules

- Staging has its own database and secrets and never holds production data.
- Local development uses `.env` (git-ignored); see `.env.example`.
