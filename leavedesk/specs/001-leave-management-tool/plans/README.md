# LeaveDesk implementation plans (index)

Source of truth: `../intent.md` and `../spec.md` (draft 2026-10-28). No code is written by these plans' authoring; they describe future PRs. Every R1–R36 is covered exactly once (see the table).

## Gate before any plan starts (not an R-number)

**C-16 / Q5 hello-world gate:** FastAPI Cloud + Supabase deploy with DB connected and cost ≤ $5/month. Due 29 Oct 2026 per the decisions log. Its result is not recorded in the spec (see A-2). Plan 01 must not merge until it passes or a budget exception is recorded.

## Plans in dependency order

| # | File | R-numbers | Phase | Depends on |
|---|---|---|---|---|
| 01 | `R-029-R-030.md` | API security baseline, audit log, backend skeleton, core tables | P1 | gate |
| 02 | `R-031.md` | Frontend shell, UX/a11y standard, SPA serving | P1 | 01 (serving only; can run parallel) |
| 03 | `R-026-R-035.md` | Email outbox + in-app notifications infrastructure | P1 | 01 |
| 04 | `R-001-R-002-R-003.md` | Login, account protection, invite/reset | P1 | 01, 02, 03 |
| 05 | `R-005-R-007-R-008.md` | Leave types, ledger, `compute_balance`, rollover/expiry jobs | P1 | 01 |
| 06 | `R-006-R-011.md` | Working-day calculation, public holidays, request tables | P1 | 01, 02, 04 |
| 07 | `R-009-R-023.md` | Employees, teams, loop check, pro-rating | P1 | 04, 05 |
| 08 | `R-024.md` | Starting balances by hand | P1 | 05, 07 |
| 09 | `R-010.md` | Balance display and sufficiency check | P1 | 05, 06 |
| 10 | `R-012-R-013-R-017.md` | Create request, validation/overlap, routing | P1 | 06, 07, 09 |
| 11 | `R-014-R-015.md` | Notice rules, Sick exemption/backdating, HR-entered leave | P1 | 10 |
| 12 | `R-016.md` | Employee cancels own Pending | P1 | 10 |
| 13 | `R-018-R-019-R-022.md` | Approve, reject, unauthorised-approver 403 | P1 | 10 |
| 14 | `R-020.md` | Cover for an absent manager | P1 | 13 |
| 15 | `R-021.md` | HR cancels Approved | P1 | 12, 13 |
| 16 | `R-004.md` | Deactivation | P1 | 07, 12 |
| 17 | `R-036.md` | Deputy HR admin | P1 | 13 |
| 18 | `R-025.md` | HR "All leave" list | P1 | 10, 13 |
| 19 | `R-032-R-033-R-034.md` | Performance, backup/restore, retention | P1 | 01 (finalise after 18) |
| 20 | `R-027.md` | Team calendar | **P2** | 13, 07 |
| 21 | `R-028.md` | Monthly report | **P2** | 13, 08, 25 data |

## Recommended execution sequence

Plans are grouped into waves. Everything inside a wave can run in parallel (separate branches off `main`); a wave starts when every plan it depends on has merged. "Needs" lists only the plans that gate the item (from the table above).

| Wave | Plans (parallel) | Needs | Why this order |
|---|---|---|---|
| **0** | C-16/Q5 gate (not a plan) | none | Decides hosting, DB and budget; nothing is built before it passes. |
| **1** | **01** R29-R30 | gate | Scaffold, core tables, CSRF/headers, audit. Every later plan reuses it. |
| **2** | **02** R31 · **03** R26-R35 · **05** R5-R7-R8 | 01 | Three independent foundations: UI primitives, notification machinery, balance engine. |
| **3** | **04** R1-R2-R3 | 01, 02, 03 | Login and invite need UI primitives and the email outbox. Unlocks all authenticated features. |
| **4** | **06** R6-R11 · **07** R9-R23 | 06: 04 · 07: 04, 05 | Working days/holidays/request tables, and employees/teams/pro-rating. |
| **5** | **08** R24 · **09** R10 | 08: 05, 07 · 09: 05, 06 | Starting balances, and balance display with the sufficiency check. |
| **6** | **10** R12-R13-R17 | 06, 07, 09 | Create request and routing. Single plan: everything after it needs it. |
| **7** | **11** R14-R15 · **12** R16 · **13** R18-R19-R22 | 10 | Notice/Sick rules, employee cancel, approve/reject. Independent of each other. |
| **8** | **14** R20 · **15** R21 · **16** R4 · **17** R36 · **18** R25 | 14: 13 · 15: 12, 13 · 16: 07, 12 · 17: 13 · 18: 10, 13 | Cover, HR cancel, deactivation, deputy, HR "All leave". |
| **9** | **19** R32-R33-R34 | 18 (merge last) | Performance is measured on the finished endpoints; sign-off for go-live. |
| **P2** | **20** R27 · **21** R28 | 20: 13, 07 · 21: 13, 08, 18 | Ship Mon 16 Nov 2026. May be started from wave 8 on spare capacity, but never ahead of P1 work. |

### Dependency chains

- **Critical path (longest chain):** gate → 01 → {02, 03} → 04 → 06 → 09 → 10 → 13 → {15, 18} → 19. Any slip here moves go-live; assign the strongest capacity to these plans first.
- **Auth chain:** 01 → 03 + 02 → 04 → (06, 07).
- **Balance chain:** 01 → 05 → {07 → 08, 09} → 10.
- **Request chain:** 10 → {11, 12, 13} → {14, 15, 16, 17, 18} → P2 {20, 21}.
- **Early-start items inside plan 19:** the backup and keep-alive workflows only need plan 01 and can be built in wave 2 on a branch, but the PR merges last (wave 9) because the perf and restore evidence needs the finished system.
- **Conformance test (plan 03):** each event-producing plan (10, 12, 13, 14, 15, 16) flips its pending marker; the last one to merge removes the final marker.

### Parallel work summary

| After this merges | These can run at the same time |
|---|---|
| 01 | 02, 03, 05 |
| 04 | 06, 07 |
| 07 and 06 (each with 05) | 08, 09 |
| 10 | 11, 12, 13 |
| 13 (and 12 for 15; 12 and 07 for 16) | 14, 15, 16, 17, 18 |
| 13 (+07), and 13 + 08 + 18 | 20, 21 |

Plans in the same wave must not both change the same files; the known shared files are `app/modules/requests/router.py`, `approvals/authz.py` and the email event catalogue. Within a wave, merge in plan-number order and rebase the rest.

### Delivery order

1. **Waves 0–3:** the system can sign people in and send mail. Gate: SendGrid sender domain verified and a real-mailbox invite received on staging (C-17); `security-review` run on the auth module (C-18).
2. **Waves 4–5:** HR can create staff and enter balances; staff see balances. Gates: holiday seed verified against the decree (A-19); anon-key-reads-nothing test green (from plan 01).
3. **Waves 6–8:** requests, approvals, cancellation, cover, deputy, HR list. This is the full P1 feature set; start entering real starting balances only after plan 08 is on production, and circulate the printable launch list for week-1 checking (C-9).
4. **Wave 9:** performance run, restore drill, retention check. Go-live review (target 1 Nov 2026; see A-2 for the schedule problem).
5. **P2:** calendar and report ship together on Mon 16 Nov 2026; HR keeps Excel for the month-end until then (C-1).

If the date cannot hold (A-2), cut by dropping *whole plans from the end of wave 8/9*, never by thinning authorization, audit or tests (CLAUDE.md). Candidates the spec itself treats as least essential for day one: 17 (deputy, only if HR can be covered otherwise: a product-owner decision), 16 (deactivation, HR can ask the developer), and 19's retention part. Plans 01–10, 12, 13 and 15 are the smallest set that lets staff request and managers decide.

Each plan includes its own UI slice, so one PR delivers a working vertical. Notification templates for an event ship in the plan that creates the event (see plan 03).

## Baseline Definition of Done (applies to every plan; plans list only extras)

- Auth, authorization and balance tests written first (CLAUDE.md). `pytest`, `ruff`, `mypy`, `vitest`, `eslint`, `tsc --noEmit` all green.
- Every new endpoint: 401 (no session), 403 (each disallowed role), strict body schema (unknown field → 4xx), `problem+json` errors, no stack traces. Built with the `add-endpoint` skill.
- Every state change writes an audit row (R-030) with no notes, reasons, tokens or Sick type.
- Sick type, notes, rejection reasons redacted on the server per §8; email/notification/log text checked.
- UI slices pass R31 (360 px, 44 px targets, AA, labels, focus on first error, confirm with default "Keep").
- Commits are conventional and cite R#/C-#; spec updated in the same PR if code and spec disagree; PR text via `pr-description`, review via `review-checklist`.
- No secrets committed; no changes under `ref/`.

## Repository layout assumed by the plans (confirm: A-1)

`app/` (FastAPI: `app/core/`, `app/modules/<name>/{router,service,repository,models,schemas,dependencies}.py`, `app/jobs/`), `migrations/` (Alembic), `tests/`, `frontend/` (Vite, build to `frontend/dist`), `.github/workflows/`.

## Ambiguity register (flagged, not decided)

Plans reference these IDs and say which behaviour they implement *only if* the spec is explicit; otherwise the item is a blocker for that step.

| ID | Ambiguity | Where | Plans |
|---|---|---|---|
| A-1 | Repo layout (`app/` vs `backend/`) is not specified. | CLAUDE.md, spec §2 | all |
| A-2 | Launch is 1 Nov (3 days from 29 Oct); 21 plans cannot fit. Which are the minimum go-live set? Also no recorded result of the Q5 gate. | intent, C-1, C-16 | all |
| A-3 | Intent line 27 says "16 managers, 1 HR"; elsewhere HR is 2 people. Intent line 51 links to a stale path `leave-management-tool/spec.md`. | intent | 17 |
| A-4 | Can HR cancel *someone else's Pending* request? §3 says HR cancels "Pending only" for own; endpoint 12 says HR may cancel "Approved or Pending". | §3, §6 #12 | 12, 15 |
| A-5 | R22 reads "returns 403 (employees/HR)": unclear wording. Is an unrelated request 403 or 404? Does an HR admin who is not an "HR approver" for non-manager requests get 403? | R22 | 13 |
| A-6 | Per-IP rate limit threshold, and how the client IP is read behind the FastAPI Cloud proxy. | R2 | 04 |
| A-7 | What is "unused" at rollover: does it count Pending (reserved) days at 31 Dec? Sick backdated into the old year after rollover, or HR adjustments after rollover? Is carry recomputed? | R7, §5.6 | 05 |
| A-8 | Pro-rating edge cases: start date in a future year, start in a prior year, start date edited later, joiners starting in January, whether `entitlement` is written for a joiner at rollover. | R9, §5.5 | 07 |
| A-9 | Notice arithmetic: "starts in less than 1 day" with calendar days in `COMPANY_TZ`: is a request for tomorrow allowed at 23:59 today? Does the 1-week warning apply to Unpaid, and to half-day starts? | R14, C-12 | 11 |
| A-10 | Who approves: an employee with no manager; a deactivated manager's reports; the deputy's own leave; a manager who is HR-less. | R17, R36 | 10, 16, 17 |
| A-11 | Deactivation edge cases: Pending requests *assigned to* the deactivated manager; deactivating the HR admin or the deputy; deactivating the only user of a team. | R4, R36 | 16 |
| A-12 | HR-entered leave (endpoint 17): are balance, overlap, notice and routing rules applied? Is the target employee notified? | R15 | 11 |
| A-13 | "Only while deciding" for notes/Sick type (cover managers): is that Pending status only? Does the direct manager keep seeing the type after the decision? | §8, C-2 | 13, 14, 18 |
| A-14 | Email/notification recipients: "HR emailed" = all HR approvers (HR admin and deputy)? Who is told when an employee cancels a Pending request in the HR queue? Is the employee also emailed on a cover approval? | R17, R26 | 03, 10, 13 |
| A-15 | R34 says history is "kept for 7 years" but defines no purge or HR-only access mechanism; `audit_log` is append-only. | R34 | 19 |
| A-16 | R32 has no measurement method or load profile for "p95 < 500 ms on the target host". | R32 | 19 |
| A-17 | R33: the "private object storage" target and CI secret handling are unspecified; restore time on the free tier unproven. | §2, R33 | 19 |
| A-18 | R24: does 0–40 apply to adjustments (signed, negative allowed)? Can opening Sick be entered? Valid range for `expires_on` of a manual carry-over? | R24 | 08 |
| A-19 | Seed holidays (Appendix A) are unverified; the verify deadline is 30 Oct. 2027 lunar dates are "approximate". | R11 | 06 |
| A-20 | R28 content: balances as of month end or run date? Columns for xlsx/csv? Is real Sick type shown (HR-only so presumably yes)? | R28 | 21 |
| A-21 | Calendar scope: which team does a manager or HR belong to? `employee.team_id` vs `team.manager_id`; employees with no team. | R27 | 20 |
| A-22 | R12 text says half-day only when start = end, then allows first/last-day halves (Q7 decided). R12 prose should be corrected. | R12 | 10 |
| A-23 | UI language (English vs Vietnamese) is not stated. | R31 | 02 |
| A-24 | Dashboard shows several carry-over blocks? Only one carry block per year exists by design; confirm. | R10 | 09 |
| A-25 | Session cookie `Secure` in local HTTP development; session sliding window behaviour on read-only calls. | R2, R29 | 01, 04 |
