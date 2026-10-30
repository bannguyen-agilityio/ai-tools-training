# Review instructions

Review-only rules for Claude Code Review. Project rules live in `CLAUDE.md` (also read by reviews); the spec in `specs/001-leave-management-tool/` is the source of truth.

## What Important means here

Reserve Important for findings that would break behavior, leak data, or weaken access control:

- Missing or wrong authorization in a service-layer function, or an endpoint without a 401/403 test per role
- Privacy leaks: Sick type, notes, rejection reasons (except to the employee), passwords or tokens in responses, emails, notifications, logs, audit rows or exports; redaction done on the client instead of the server
- Balance rules outside `compute_balance`, or a stored balance that should be derived
- `balance_entry` or `audit_log` updated or deleted instead of appended; app role granted UPDATE/DELETE on append-only tables
- Missing `version` check (stale must return `409`), submit without the `FOR UPDATE` employee lock, or anything that breaks the `leave_request_day` overlap index
- Approving one's own request, or approver routing that deviates from the rules in `CLAUDE.md`
- Cancel rules broken (employee only while Pending, HR only once Approved, refund exactly once), a rejection without a 1-500 char reason, or Sick entry allowed more than 7 days back for non-HR
- A manager able to see a report's balance
- A new table without a test that the anon key reads nothing
- Authorization, audit or tests removed or skipped to hit a date
- Non-parameterised SQL, request schemas that accept unknown fields, secrets committed, `EMAIL_BACKEND=mock` allowed in production
- Migrations that add a second Alembic head, or a table without RLS enabled (and no policies)
- Date logic ("today", notice, year boundary, holidays) that is not converted to `COMPANY_TZ` before comparing
- Report/export without HR-only check, audit entry, or formula escaping

Style, naming and refactoring suggestions are Nit at most.

## Escalate

- Any violation of the Privacy section of `CLAUDE.md` is Important.
- A new or changed `Settings` field that does not update `.env.example`, `docs/runbooks/secrets.md`, `tests/test.env` and every `leavedesk-*` workflow listed in `CLAUDE.md` (under `../.github/workflows/`, outside this directory) is Important. So is a secret set at repo level instead of a GitHub environment, or not scoped to the step that needs it.
- A behavior change that contradicts the spec without a matching spec edit in the same PR is Important.

## Cap the nits

Report at most five Nits per review.

## Do not report

- Anything CI already enforces: ruff, formatting, mypy, pyright, eslint, `tsc`
- `uv.lock`, `frontend/package-lock.json` and other lockfiles
- Anything under `ref/` (stale training material)
- Existing drift already recorded in `CLAUDE.md` (`problem+json` errors vs spec §6.1, Python 3.12 vs 3.14) unless the PR makes it worse
- Test-only code that intentionally breaks production rules (for example fixtures that bypass redaction)

- Minor findings in `scripts/` (only report if near-certain and severe), except `scripts/check_single_head.py`, which guards the single Alembic head

## Always check

- New endpoints have a 401/403 test per role (Important when missing)
- New or changed error handling uses `{ "error": { code, message, details[] } }`; `error.stack` only outside production
- Quantities are `numeric(4,1)` in 0.5 steps; ids are uuid; timestamps are `timestamptz` UTC
- Email bodies, notifications, log lines, audit details and exports contain no Sick type, notes, passwords or tokens, and rejection reasons only go to the employee (email addresses in the outbox are fine)
- Dates in UI and email text are unambiguous ("Mon 2 Nov 2026"); UI changes keep 44 px targets and labelled fields
- Feature and behavior PRs cite R# / C-# numbers (not needed for docs-only or CI-only PRs)

## Evidence

Behavior claims need a `file:line` citation in the source, not an inference from naming. Privacy and authorization findings must name the role or caller affected and the data exposed.
