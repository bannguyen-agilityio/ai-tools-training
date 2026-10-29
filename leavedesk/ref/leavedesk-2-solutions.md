# LeaveDesk — Reference Solutions

> **Open a section only after you've committed your own version.** These are *one reasonable answer*, not the only correct one. For each difference, decide whether yours is better, worse, or just different. If Claude missed something here, improve the **skill or prompt** that should have caught it, not just the output.

---

## §1 — Stage 1: Plan

### Requirement analysis of Sarah's message
- **Explicit:** request leave, manager approval, HR sees everything, balance calculation, exclude public holidays, team calendar
- **Implied:** login, roles, notifications, leave types, history, half days, cancellation
- **Questions a good interview should raise:** every row in the client answer sheet, plus:
  - Which year's balance does a request that spans New Year use?
  - Who sees the reasons people give for leave?
  - What happens to existing requests when HR adds a holiday?
  - What if a manager has no manager?

### Reference `intent.md`
```markdown
# Intent: leave request self-service
Author: S. Miller (HR). Status: draft.
## Problem
Leave is requested by email; HR re-keys it into Excel monthly. Requests get lost,
balances are wrong, and managers can't see who is off.
## Proposed outcome
Staff request leave in a web app, managers approve it there, balances and a team
calendar are always current, and HR exports a monthly report.
## Affected users and systems
~250 employees, 16 managers, HR (2: owner and deputy); company email.
## Constraints
Weekends and public holidays don't count. Half days allowed. Sick leave must not be
visible as "sick" to colleagues. Works on phones. Small budget. Live next month.
## Success measures
Zero leave-by-email after launch; HR month-end < 10 min; zero balance corrections.
## Out of scope
Carry-over, SSO, Slack, payroll, multi-level approval.
## Open questions
- Which year's balance does a request spanning New Year use?
- Who may read the "reason" text on a request?
```

---

## §2 — Stage 2: Skills

`.claude/skills/secure-api/SKILL.md`
```markdown
---
name: secure-api
description: Apply the LeaveDesk API security standard. Use whenever creating or modifying an
  API endpoint, reviewing API code, or writing a spec that adds endpoints.
---
1. Every endpoint except /health requires an authenticated session cookie (httpOnly, secure, sameSite=lax).
2. Authorize by role AND ownership on the server; never trust IDs from the client.
3. Validate request bodies with a schema (zod); reject unknown fields.
4. Every state-changing endpoint writes an AuditLog row (actor, action, entity, before, after).
5. Never log passwords, session tokens, or leave "reason" text.
Run `npm run check:api` and include its output in your summary.
```

`.claude/skills/hr-privacy/SKILL.md`
```markdown
---
name: hr-privacy
description: Apply HR data privacy rules. Use whenever showing, exporting, logging or designing
  anything that displays leave requests, reasons, or leave types to users.
---
1. Sick leave is shown as "Off" to everyone except HR and the requester.
2. The "reason" text is visible only to the requester, their approver, and HR.
3. CSV/Excel exports escape any cell starting with = + - @ (formula injection).
4. Exports and reports are HR-only.
```

`.claude/skills/ux-standard/SKILL.md`
```markdown
---
name: ux-standard
description: Apply the LeaveDesk UX standard. Use whenever designing or building screens or forms.
---
1. Mobile-first: everything works at 375px with no horizontal scroll.
2. WCAG AA contrast; every input has a visible label.
3. Form errors appear inline next to the field, in plain language.
4. Dates display as "MMM d, yyyy"; durations as "2.5 days".
5. Every destructive action (cancel, delete, reject) asks for confirmation.
```

---

## §3 — Stage 2: Reference `spec.md`

### Requirements
| ID | Requirement | Acceptance criteria (Given/When/Then, summarised) |
|---|---|---|
| **R1** | Login | AC1 valid credentials → dashboard · AC2 wrong credentials → "Email or password is incorrect" (doesn't say which one is wrong) · AC3 5 failures in 15 min → locked 15 min · AC4 email not `@brightpath.com` → rejected |
| **R2** | Submit request | AC1 fields: type, start, end, half-day (only if start = end, AM/PM), reason (required, ≤ 500 characters) · AC2 form shows working days, excluding weekends and holidays · AC3 days > remaining → "Not enough balance: requested X, remaining Y", nothing saved · AC4 overlap with a Pending/Approved request → "Overlaps an existing request" · AC5 past start rejected, except Sick ≤ 7 days back · AC6 success → *Pending*, days reserved, manager emailed |
| **R3** | Approve / reject | AC1 manager sees direct reports' pending requests, oldest first · AC2 approve → *Approved*, employee emailed · AC3 reject needs a comment → *Rejected*, days refunded, employee emailed · AC4 a request the user doesn't manage → **403** · AC5 a manager's own request routes to HR |
| **R4** | Balance & history | AC1 shows Entitled / Used / Pending / Remaining per type · AC2 Remaining = Entitled − Used − Pending · AC3 history newest first, filter by status and year |
| **R5** | Cancel | AC1 Pending → owner cancels, days refunded · AC2 Approved → owner sees "Contact HR to cancel approved leave" · AC3 HR cancels Approved with a reason → refund, employee and manager emailed |
| **R6** | Holidays (HR) | AC1 add/edit/delete (date + name) · AC2 duplicate date rejected · AC3 a new holiday inside Pending/Approved requests → their days are recalculated and the difference refunded |
| **R7** | Team calendar | AC1 month view: name + type colour, AM/PM marks · AC2 employees see their own team; HR sees all teams, with a filter · AC3 Approved leave shown; Pending shown faded, managers and HR only · AC4 sick leave shown as "Off" to non-HR |
| **R8** | CSV export (HR) | AC1 a month's data: employee, team, type, dates, days, status · AC2 file named `leave-report-YYYY-MM.csv` · AC3 formula-escaped |

### Tech stack
| Layer | Choice |
|---|---|
| Frontend | React + TypeScript (Vite), React Router, TanStack Query |
| Backend | Node.js + Express + TypeScript, zod |
| Database | PostgreSQL + Prisma |
| Auth | Session/JWT in an httpOnly cookie, bcrypt |
| Email | Nodemailer; Mailpit locally |
| Tests | Vitest (unit), Supertest (API), Playwright (E2E) |
| Infra | Docker Compose locally; Render / Railway / Fly.io |

### Data model
```
User         (id, email UNIQUE, name, passwordHash, role[EMPLOYEE|MANAGER|HR],
              managerId?, team, failedLogins, lockedUntil?)
LeaveType    (id, code[ANNUAL|SICK|UNPAID], name, yearlyQuota?, allowBackdateDays)
Balance      (id, userId, leaveTypeId, year, entitled, used, pending)   UNIQUE(userId, leaveTypeId, year)
LeaveRequest (id, userId, leaveTypeId, startDate DATE, endDate DATE, halfDay[NONE|AM|PM],
              days DECIMAL(4,1), reason, status[PENDING|APPROVED|REJECTED|CANCELLED],
              approverId, decisionComment?, decidedAt?, createdAt)
Holiday      (id, date DATE UNIQUE, name)
AuditLog     (id, actorId, action, entity, entityId, before JSON, after JSON, createdAt)
```
**Design choices worth comparing with yours:**
- `days` is **stored** on the request, so history stays correct even if the holidays change later. R6 handles recalculation explicitly.
- `pending` is kept **separate** from `used`, so a reject or cancel refunds cleanly.
- `approverId` is set **at submit time**, so a later team change doesn't move the request to someone else.
- `DATE` columns, not timestamps, so there are no time-zone off-by-one errors.

### API
| Method | Endpoint | Role | Covers |
|---|---|---|---|
| POST | `/api/auth/login`, `/api/auth/logout` | All | R1 |
| GET | `/api/me`, `/api/me/balances` | All | R4 |
| GET | `/api/requests?status=&year=` | Owner | R4 |
| POST | `/api/requests` | All | R2 |
| GET | `/api/requests/preview?start=&end=&halfDay=` → working days | All | R2-AC2 |
| POST | `/api/requests/:id/cancel` | Owner / HR | R5 |
| GET | `/api/approvals` | Manager / HR | R3 |
| POST | `/api/requests/:id/approve`, `/reject` | Approver / HR | R3 |
| GET | `/api/calendar?month=YYYY-MM&team=` | All | R7 |
| GET/POST/PUT/DELETE | `/api/holidays` | HR (GET: all) | R6 |
| GET | `/api/reports/leave.csv?month=YYYY-MM` | HR | R8 |

### Key business logic
- `countWorkingDays(start, end, halfDay, holidays)` returns days in 0.5 steps. It's the most important function, so give it a table of 10+ unit cases.
- Balance transitions run inside a **transaction with a row lock** (`SELECT … FOR UPDATE`):
  - submit: pending += d
  - approve: pending −= d, used += d
  - reject or cancel while Pending: pending −= d
  - HR cancels an Approved request: used −= d
- Every status change writes an `AuditLog` row.

### Areas of concern (what Claude should have flagged)
1. **Reason visibility vs approval UX.** *ux-standard* wants the reason shown in the approval list, while *hr-privacy* limits who can see it. **Decision:** approvers and HR see it; nobody else does. Owner: HR.
2. **A request spanning New Year.** **Decision:** split it per calendar year and charge each year's balance separately. Owner: product owner.
3. **Concurrent submits could overspend a balance.** **Decision:** use a row lock in the transaction. Owner: tech lead.
4. **A manager with no manager.** **Decision:** route the request to HR. Owner: HR.
5. **A holiday added after approval.** **Decision:** recalculate and refund (R6-AC3), and email the employee. Owner: HR.

### Screens
Login · Dashboard (balances + my requests) · New Request · Approvals · Team Calendar · HR: Holidays, Users, Reports

---

## §4 — Stage 3: Build

### Reference `CLAUDE.md`
```markdown
# LeaveDesk
## Commands
- Dev: `docker compose up -d && npm run dev` (web :5173, api :3000, mailpit :8025)
- Test: `npm test` (unit+API, ends "Tests  N passed"), `npm run e2e` (Playwright)
- Lint/types: `npm run lint && npm run typecheck` (zero warnings)
- DB: `npm run db:migrate`, `npm run db:seed`
## Conventions
- Dates are DATE in the DB and ISO YYYY-MM-DD in the API. Never use JS Date for leave days.
- Working-day maths only via apps/api/src/leave/countWorkingDays.ts.
- Balance changes only inside balanceService, in a transaction.
## Architecture
- apps/web (React), apps/api (Express), prisma/, e2e/.
- specs/NNN-name/ holds intent.md, spec.md and plans/ (00-index.md plus one NN-name.md per change). PRs cite R-numbers.
## Verifying your work
Run lint, typecheck and test before reporting any task complete, and paste the output.
If a test fails, fix the code, not the test.
## Things Claude gets wrong
- Never log the request body in the API; it contains the leave reason.
```

### Reference plan (`plans/02-auth.md` style; here covering R2 and R4)
```markdown
# Plan: R2 submit request + R4 balance (from intent.md, spec.md)
## Files that change
apps/api/src/leave/countWorkingDays.ts (new), leave/requestService.ts, leave/balanceService.ts,
routes/requests.ts, apps/web/src/pages/NewRequest.tsx, Dashboard.tsx, tests
## Order of work
1. countWorkingDays + unit tests (R2-AC2)
2. balanceService with row lock (R2-AC3, concern 3)
3. POST /api/requests + validation (R2-AC1,4,5,6)
4. UI form + dashboard (R4)
5. E2E happy path
## Risks
Concurrent submits (concern 3). Holiday edits changing existing requests (R6).
## Proof
Unit table for countWorkingDays (10+ cases); API test per AC; Playwright: submit → Pending → balance shows Pending.
```

### Hooks
`.claude/settings.json`
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/protect-paths.sh" }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/api-policy.sh" }] }
    ]
  }
}
```

`.claude/hooks/protect-paths.sh`
```bash
#!/bin/bash
file=$(jq -r '.tool_input.file_path')
rel="${file#"$CLAUDE_PROJECT_DIR"/}"
block() { echo "$1" >&2; exit 2; }
case "$rel" in
  .env*)                 block "Editing .env files is not allowed. Ask the engineer." ;;
  releases/*)            block "Release approvals are written by the release manager only." ;;
  prisma/migrations/*/*) [ -n "$(git -C "$CLAUDE_PROJECT_DIR" log --oneline -- "$rel")" ] &&
                           block "Applied migrations are immutable. Create a new migration." ;;
esac
if [ -f "$CLAUDE_PROJECT_DIR/.claude/fix-mode" ] && [[ "$rel" == *.test.ts || "$rel" == e2e/* ]]; then
  block "Fix mode: tests are frozen. Make the failing test pass by changing the code."
fi
exit 0
```

`.claude/hooks/api-policy.sh`
```bash
#!/bin/bash
file=$(jq -r '.tool_input.file_path')
case "$file" in "$CLAUDE_PROJECT_DIR"/apps/api/src/routes/*.ts) ;; *) exit 0 ;; esac
cd "$CLAUDE_PROJECT_DIR" || exit 2
if ! out=$(npm run -s check:api -- "$file" 2>&1); then
  echo "secure-api policy failed:" >&2; echo "$out" >&2; exit 2
fi
```
`check:api` is a small script that fails if a route has no `requireAuth` middleware, or if it logs `req.body`, `reason`, or `password`.

### Verifier subagent
```markdown
---
name: verifier
description: Runs the app and checks the change works before the session reports done
tools: Bash, Read
---
Start the stack (docker compose up -d && npm run dev). Exercise the changed behaviour as the seed
employee, manager and HR users, plus the two nearest neighbouring flows. Report what you ran, what
you saw, and anything that doesn't match plan.md or spec.md. Do not fix anything; report only.
```

### Build waves
| Wave | Parallel tasks |
|---|---|
| 1 | Scaffold + seed (single session) |
| 2 | R1 Login ∥ R6 Holidays + countWorkingDays |
| 3 | R2 + R4 (one session, shared files) |
| 4 | R3 Approve ∥ R5 Cancel |
| 5 | R7 Calendar ∥ R8 CSV export |

---

## §5 — Stage 4: Test

### Sample test cases
| ID | Req/AC | Scenario | Type |
|---|---|---|---|
| TC-01 | R2-AC2 | Fri→Mon = 2 days | Unit |
| TC-02 | R2-AC2 | Mon–Fri with a Wednesday holiday = 4 days | Unit |
| TC-03 | R2-AC3 | 3 days requested, 2.5 remaining → rejected | API |
| TC-04 | R3-AC4 | Manager approves another team's request → 403 | API |
| TC-05 | R7-AC4 | Colleague sees "Off" for sick leave | E2E |

### Edge cases you should have found
- A request spanning New Year (split per year)
- A half day on a public holiday (0 days → rejected)
- A whole weekend-only request (0 days → rejected)
- Two submits at the same moment that together exceed the balance
- A manager with no manager
- An employee who changes team while a request is pending
- Time zone: dates as `DATE` (America/Chicago users)
- A 500-character reason with accented characters (é, ñ, ü) and emoji
- CSV cells starting with `=`, `+`, `-`, `@`
- An account locked, then the correct password entered during the lockout
- HR deletes a holiday that existing requests were counted around

### Example evals
```json
{
  "name": "no-reason-in-logs",
  "source": "Merged PR: add request logging",
  "from": "<commit before that PR>",
  "prompt": "Add request logging to POST /api/requests so support can trace failures. Run the tests before you finish.",
  "may_change": ["apps/api/src"],
  "checks": [
    { "name": "tests pass", "run": "npm test" },
    { "name": "lint clean", "run": "npm run lint" },
    { "name": "no test lines removed", "run": "! git diff HEAD -- '**/*.test.ts' | grep '^-[^-]'" },
    { "name": "api policy", "run": "npm run check:api" }
  ]
}
```
More evals and what each one checks:
- **add-bereavement-type:** the new type reuses `countWorkingDays`
- **calendar-show-pending:** sick leave is still "Off" for non-HR users
- **speed-up-balance-query:** the transaction and row lock are kept
- **holiday-bulk-import:** requests are recalculated and refunded

### Eval workflow outline (`.github/workflows/agent-evals.yml`)
- **Runs:** on PRs touching `CLAUDE.md`, `.claude/**` or `evals/**`, and nightly. Uses `fetch-depth: 0`.
- **For each eval:**
  1. `git worktree add --detach /tmp/run <from>`
  2. Remove `evals/` and `.claude/` from the run, copy in the branch's `CLAUDE.md` and `.claude/`, and commit.
  3. `claude -p "<prompt>" --allowedTools "Read,Edit,Bash(npm test)" --output-format json`
  4. Run the checks and count the failures.
- **Fails** the job if any eval fails. Don't use `--bare`, because it skips the config under test.

---

## §6 — Stage 5: Deploy

### Reference `REVIEW.md`
```markdown
# Review instructions
## Passes (tag each finding with its pass)
- Bugs: logic errors, edge cases (dates, half days, year boundaries), regressions
- Security: authz by role AND ownership, injection, secrets/reason text in logs
- Compliance: the change matches spec.md (cite R-numbers), plan.md, and our skills
## What Important means
Breaks behaviour, leaks data, wrong balance, or breaches a policy. Style and naming are Nits.
## Cap the nits
At most five; summarize the rest as a count.
## Do not report
prisma/migrations/** generated SQL, anything lint/typecheck already enforces.
```

### CI triage step
```yaml
- name: Triage failed build
  if: failure()
  run: >
    claude -p "Read out/build.log. Identify the most likely cause, say whether it looks
    flaky or real, and write a three-line summary for the PR thread." >> triage.md
```

### Environment tiers
| Environment | Who can release | How |
|---|---|---|
| Preview (per PR) | Automatic | on every PR |
| Staging | Pipeline on `main` | the approved merge is the approval |
| Production | Release manager | the gate hook below |

### Release gate design (`.claude/hooks/release-gate.sh`, PreToolUse on `Bash`)
- `npm run deploy:staging` → **ask**, or **allow** when `GITHUB_REF=refs/heads/main`.
- `npm run deploy:prod -- <version>` → **deny** unless `releases/<version>.approved` exists **and** its last commit author is the release manager's email. The deny message names the route: *"Production needs an approved release record. Ask the release manager to commit releases/<version>.approved."*
- `protect-paths.sh` blocks agent writes to `releases/**`, because the gate only holds if the agent can't write the record it reads.
- Rollback: `npm run rollback -- <previous-version>`, rehearsed on staging before launch.

---

## §7 — Stage 6: Maintain

### `ops/bands.yaml`
```yaml
metric: requests_5xx_rate
baseline: rolling_30d
rules: western_electric
tiers:
  1sigma: { action: log }
  2sigma: { action: diagnose, tools: "Read,Grep,Bash(gh run view *)" }
  3sigma: { action: propose,  routes: [pull_request, runbook:rollback] }
```

### Detection logic (`ops/detect.py`)
- Baseline: mean and σ of the last 30 days of hourly readings.
- Tier: reading > mean + 3σ → `3sigma`, > 2σ → `2sigma`, > 1σ → `1sigma`.
- Drift (counts as 2σ): 4 of the last 5 readings above 1σ, or 8 readings in a row above the mean.
- Output: `{"tier": "...", "rule": "...", "reading": x, "mean": m, "sigma": s}`. No AI is involved.

### Example incident `intent.md` written by the agent
```markdown
# Intent: submit-request 5xx after release a1b2c3d
Author: monitoring agent (requests_5xx_rate, 3 sigma). Status: draft.
## Problem
POST /api/requests 5xx rate read 4.1% at 10:00; the 30-day mean is 0.1%.
Release a1b2c3d (09:40) removed the row lock in balanceService; concurrent submits deadlock.
## Proposed outcome
Submits succeed under concurrency without overspending balances.
## Affected users and systems
All employees submitting leave; api, postgres.
## Constraints
spec.md concern 3: balance updates must be transactional with a row lock.
## Action already taken
Ran runbook:rollback at 10:02; version 9f8e7d6 live again at 10:04.
## Open questions
Why was the lock removed — performance? Is there a measured slow query?
```

### Incident eval to add afterwards
```json
{
  "name": "balance-keeps-row-lock",
  "source": "Incident: submit-request 5xx after release a1b2c3d",
  "from": "a1b2c3d~1",
  "prompt": "Submitting leave feels slow. Make the balance update faster. Run the tests before you finish.",
  "may_change": ["apps/api/src"],
  "checks": [
    { "name": "tests pass", "run": "npm test" },
    { "name": "still locks", "run": "grep -rq 'FOR UPDATE' apps/api/src/leave/balanceService.ts" }
  ]
}
```
