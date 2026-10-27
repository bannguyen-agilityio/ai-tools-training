# cicd-deploy-lab

Practice project for **"CI/CD integration and deployment"**
(The AI-Native SDLC Playbook). Pure Python 3, no dependencies. Sub-folder of a bigger repo.

## Pipeline

```
PR  ──► ci (tests, lint, deploy --dry-run) ──► Claude review (claude-code-review.yml)
main ─► ci ─► deploy-staging (auto) ─► smoke ─► deploy-production (HUMAN approval) ─► smoke
```

Workflow: `.github/workflows/cicd-deploy-lab.yml` (repo root, scoped to this folder).

## Step 0 — run locally
```bash
cd cicd-deploy-lab
python3 -m unittest
python3 scripts/deploy.py production --dry-run
python3 scripts/deploy.py staging && python3 scripts/smoke.py staging
```

## Setup (once, on GitHub)
1. Settings > Environments > create `staging` (no rules) and `production`
   (**Required reviewers** = you; optionally restrict to `main`).
2. Secret `CLAUDE_CODE_OAUTH_TOKEN` is already used by the existing review workflow.

## Exercises
1. **Green path.** Branch, change `VERSION` in `app/version.py`, open a PR. Watch `ci` and the Claude review. Merge; watch staging auto-deploy and production *wait*. Approve it.
2. **Red CI.** Break a test on a branch. Confirm the PR fails and nothing deploys. Ask Claude Code to fix it, push, confirm green.
3. **Smoke gate.** Make `health()` return `status: "down"`. Confirm `deploy.py` aborts, staging fails, production never starts.
4. **Reject at the gate.** Reject the production approval. Check the run ends cleanly and staging stays deployed.
5. **AI in the pipeline (homework).** Add a job that runs `claude -p` (via `anthropics/claude-code-action`) to write release notes from `git log` into the job summary. Keep it read-only (`permissions: contents: read`) and never let it trigger the deploy.
6. **Rollback (homework).** Add a `workflow_dispatch` input `version` and a rollback job that redeploys a previous tag to production through the same approval gate.

## Measure
- Leading: PR → green time; time production waits for approval.
- Lagging: failed deploys, rollbacks, change-failure rate per month.
