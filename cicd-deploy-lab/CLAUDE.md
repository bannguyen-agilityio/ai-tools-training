# cicd-deploy-lab
- Test: `python3 -m unittest` (run from this folder). Lint: `ruff check .`
- Never edit `.github/workflows/` production-deploy job approvals; production requires the `production` environment reviewers.
- Deploy only via `scripts/deploy.py`; always `--dry-run` first.
