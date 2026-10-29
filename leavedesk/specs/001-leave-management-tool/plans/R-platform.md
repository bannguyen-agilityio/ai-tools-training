# Plan 00: Platform (environments, deploy pipeline, DB operations, scheduled-job workflows)

Phase P1. Depends on: C-16/Q5 gate. Blocks: staging DoD of plan 01, the staging gates of plans 04 and 19, and every Playwright-on-staging check. No R-number (scaffold plan, like the scaffold part of plan 01).

## Requirements and acceptance criteria

Source: spec §2 (hosting, database, tests), §5.6 (scheduled jobs), C-16, C-17, Q5, Q13. CLAUDE.md: hosting, jobs, secrets, "Playwright against staging".

- **Environments:** `staging` and `production` on FastAPI Cloud, each with its own database and secrets. Staging never holds production data.
- **Secrets:** database URL (pooled), SendGrid key, session key, `COMPANY_TZ`, `EMAIL_BACKEND` are platform environment variables or GitHub Actions secrets. None are committed.
- **Deploy:** CI builds the Vite bundle, then `fastapi deploy` ships backend and SPA as one service. Staging on merge to `main`; production only after manual approval.
- **Migrations:** `alembic upgrade head` runs before the new version takes traffic; a failed migration fails the deploy. Exactly one Alembic head.
- **Rollback:** redeploy the previous tag; rehearsed on staging before go-live.
- **Production guard:** the app refuses to start with `EMAIL_BACKEND=mock` when `ENVIRONMENT=production`.
- **Scheduled jobs:** each `python -m app.jobs.<name>` has a cron workflow using the production `DATABASE_URL`; no job endpoint is exposed; all jobs idempotent; runs do not overlap.
- **Gate record:** the Q5 hello-world result (monthly cost, DB connected, CI scheduling and background-task support) is written into the spec (closes the gap in A-2).

## Files

Create: `.github/workflows/{deploy.yml,job.yml}` (`job.yml` is a reusable `workflow_call` workflow); `.github/workflows/jobs-<name>.yml` thin callers added by the plan that owns each job; `docs/runbooks/{deploy,rollback,secrets}.md`; `scripts/check_single_head.py`; `tests/test_prod_guard.py`.
Modify: `app/core/config.py` (add `ENVIRONMENT`, mock-email guard; created by plan 01); `specs/001-leave-management-tool/spec.md` (record gate result in §2/§13, and any decision on A-26 to A-28); `.env.example` only if a new variable is needed (owned by plan 01).
Delete: none.

## Steps (in order)

1. Run the Q5 hello-world: FastAPI Cloud service + Supabase (Singapore, free tier), DB connected through the pooler. Record cost, region, rollback options, whether scheduled CI and in-process background tasks work (A-28). If total > $5/month, stop and request the budget exception (C-16).
2. Decide staging DB topology (A-26) and create the staging and production services and databases. Record the decision in the spec.
3. Write failing test first: `tests/test_prod_guard.py` (app start with `ENVIRONMENT=production` and `EMAIL_BACKEND=mock` raises).
4. Implement the guard in `app/core/config.py`.
5. `scripts/check_single_head.py` (fails if Alembic has more than one head); run it in CI.
6. Secrets inventory in `docs/runbooks/secrets.md`: name, where it lives (platform env or GitHub secret), who can rotate it. No values.
7. `deploy.yml`: on push to `main` → install, build `frontend/`, run migrations against staging, `fastapi deploy` staging, `/healthz` check, Playwright smoke. A `production` job behind a GitHub environment with required reviewer repeats the same steps against production.
8. Rollback: tag every production deploy; `docs/runbooks/rollback.md` describes redeploying the previous tag and what to do about a migration that already ran (forward-fix by default; down-migrations only if tested). Rehearse on staging.
9. `job.yml` reusable workflow: inputs `module`, `schedule`; `concurrency` group per job, `timeout-minutes`, failure notification to the developer; supports `workflow_dispatch` for manual runs.
10. Document the cadence table for jobs (rollover/expiry daily; outbox drain per minute or in-process; keep-alive daily; backup nightly) and which plan adds each caller.
11. Update the spec with the gate result and decisions (same PR).

## Risks and dependencies

- Q5 may fail → hosting redesign or budget exception (C-16). Nothing else starts until it passes.
- Free-tier Supabase pauses inactive projects and has weak backups (Q13); mitigation sits in plan 19 (keep-alive, `pg_dump`). A second free project for staging may be refused (A-26).
- GitHub Actions cron is best-effort (delays of several minutes, can be disabled after 60 days of repo inactivity); per-minute outbox draining may need the in-process task instead (A-28).
- Production `DATABASE_URL` in GitHub secrets widens who can reach HR data; limit to the production environment and required reviewers (A-27).
- Personal-account ownership of Supabase is an accepted risk (Q13).
- A-1 (repo layout) is unresolved: paths above assume `app/`, `migrations/`, `frontend/`.

## Tests proving each criterion

| Criterion | Evidence |
|---|---|
| Production guard | `tests/test_prod_guard.py`: mock backend + production → start fails; other combinations start |
| Single migration head | `scripts/check_single_head.py` runs in CI; a branch with two heads fails |
| Migrations on deploy | staging deploy log shows `alembic upgrade head` before traffic; an intentionally failing migration aborts the deploy (rehearsal) |
| Deploy pipeline | merge to `main` deploys staging; `/healthz` 200 and Playwright smoke green; production job waits for approval |
| Rollback | rehearsal on staging: deploy bad tag, redeploy previous tag, `/healthz` 200 and data intact |
| Job workflows | `workflow_dispatch` run of a caller succeeds twice in a row with identical end state (idempotent); overlapping runs queue, not run in parallel |
| No secrets committed | secret scan in CI passes; `docs/runbooks/secrets.md` lists names only |

## Definition of done

- Baseline DoD (README) where applicable, plus: staging and production exist and are reachable, deploy and rollback rehearsed and documented, gate result and topology decisions written into the spec, `job.yml` available for plans 03, 05 and 19 to call, no secret in the repo.
