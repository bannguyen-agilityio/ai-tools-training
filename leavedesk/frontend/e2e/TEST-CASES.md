# LeaveDesk end-to-end test cases (Playwright)

Draft for review. IDs are stable (`E2E-<area>-<n>`); each becomes one `test()` in `e2e/<area>.spec.ts`.
Priority: **P0** = go-live gate (1 Nov), **P1** = should pass at launch, **P2** = calendar/report.
Default viewport 360 x 640 (R31). Unless stated, "sees" means visible on screen, not just in the API.

## 0. Setup assumptions (to confirm)

- Run against a seeded staging or a local stack with `EMAIL_BACKEND=mock`; emails and invite links are read from the outbox via a test-only helper, not a mailbox.
- Fixed "today" is not available in the browser, so dates are computed relative to the real today in `Asia/Ho_Chi_Minh` (next working day, +10 working days, etc.).
- One persona per role, created by a seed script: `employee1`, `employee2` (same manager), `employee3` (other manager), `mgr1`, `mgr2`, `hr1`, `hr2`, `deputy`.
- Each test creates its own requests and cleans up by cancelling; tests do not depend on order.
- Not built yet, so skipped until built: notification bell UI, HR Audit log screen, HR "Enter leave" form, HR employee-deactivation reassignment.

## 1. Auth and account (R1, R2, R3)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-AUTH-1 | P0 | Sign in with valid company email and password | Lands on Dashboard; name shown; session cookie is HttpOnly (not in `document.cookie`) |
| E2E-AUTH-2 | P0 | Wrong password, unknown email | Same generic message for both; no hint which field is wrong |
| E2E-AUTH-3 | P0 | Email outside the company domain (e.g. `@gmail.com`) | Refused with a clear message |
| E2E-AUTH-4 | P0 | Repeated failures | Lockout/throttle message per R2; correct password still blocked during lockout |
| E2E-AUTH-5 | P0 | Visit any protected route signed out | Redirected to sign-in; after sign-in returns to the route |
| E2E-AUTH-6 | P0 | Sign out, press browser Back | Protected content not shown |
| E2E-AUTH-7 | P0 | Invite link: set password, then sign in | Works once; reusing the link fails |
| E2E-AUTH-8 | P1 | Password reset: request, use link, sign in with new password | Old password rejected; link single-use; request for unknown email shows the same message |
| E2E-AUTH-9 | P1 | Weak/short password on set or reset | Field error, focus moves to the field |
| E2E-AUTH-10 | P0 | Deactivated user signs in / has an open session | Sign-in refused; open session ends on next request |

## 2. Dashboard and balances (R5, R7, R8, R10)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-DASH-1 | P0 | Employee with entitlement 12 sees Annual and Sick cards | Entitlement, carried, used, reserved, available shown; Unpaid has no balance card |
| E2E-DASH-2 | P0 | Submit a Pending request | Reserved rises and Available falls by working days; Used unchanged |
| E2E-DASH-3 | P0 | Pending request approved | Reserved becomes Used |
| E2E-DASH-4 | P0 | Pending rejected or cancelled | Days returned to Available |
| E2E-DASH-5 | P1 | Employee with carried days | Carried block and its expiry date (e.g. "Thu 31 Dec 2027") shown; carried days consumed first |
| E2E-DASH-6 | P1 | Manager with pending items | Pending-approval count shown and links to Approvals |
| E2E-DASH-7 | P1 | Upcoming leave list | Shows own Approved leave in date order |
| E2E-DASH-8 | P0 | Manager opens a report's balance (UI/URL) | Not visible (403/empty); managers cannot see reports' balances |

## 3. New request (R6, R12, R13, R14, R15)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-REQ-1 | P0 | Annual, Mon-Fri next week, valid | Live day count 5; balance-after shown; submit succeeds; appears in My requests as Pending |
| E2E-REQ-2 | P0 | Range spanning a weekend | Working days exclude Sat/Sun |
| E2E-REQ-3 | P0 | Range spanning a seeded public holiday | Holiday excluded from the count |
| E2E-REQ-4 | P0 | Half day (single day AM/PM) | Count 0.5; start/end parts consistent |
| E2E-REQ-5 | P1 | Multi-day with first day PM and last day AM | Count reduced by 0.5 each end; AM start / PM end refused |
| E2E-REQ-6 | P0 | End before start | Field error; focus on first error |
| E2E-REQ-7 | P0 | Overlap with own Pending or Approved leave | Blocked with the overlapping dates named |
| E2E-REQ-8 | P0 | Start in the past (Annual) | Blocked |
| E2E-REQ-9 | P0 | Sick up to 7 days back | Accepted; 8+ days back refused (HR only) |
| E2E-REQ-10 | P0 | Annual request exceeding available | Blocked with available shown |
| E2E-REQ-11 | P0 | Single-day Annual/Unpaid starting today | Hard block (notice < 1 day); tomorrow allowed |
| E2E-REQ-12 | P1 | More than 5 working days starting within 7 days | Warning shown, submit still allowed; warning shown to approver |
| E2E-REQ-13 | P0 | Sick leave starting today | No notice block or warning |
| E2E-REQ-14 | P1 | Unpaid | No balance-after; accepted |
| E2E-REQ-15 | P1 | Spans 31 Dec to 2 Jan | Per-year deduction shown for both years |
| E2E-REQ-16 | P0 | Double-click submit | One request only |
| E2E-REQ-17 | P1 | Note over the maximum length | Field error |
| E2E-REQ-18 | P0 | Employee with no active manager | Clear refusal, nothing saved |
| E2E-REQ-19 | P0 | Manager submits | Routed to HR; HR admin's request routed to deputy |
| E2E-REQ-20 | P1 | Date field accepts "Mon 2 Nov 2026" typed and rejects gibberish | ISO round trip; helpful error |

## 4. My requests, detail, cancel (R16, R21)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-MY-1 | P0 | List shows own requests with status; none from others | Correct statuses and dates |
| E2E-MY-2 | P0 | Open own request detail | Dates, type, days, status, note |
| E2E-MY-3 | P0 | Open another employee's request URL | "You cannot view this request" |
| E2E-MY-4 | P0 | Cancel Pending: dialog default focus on "Keep" | Keep closes without change; Cancel releases days |
| E2E-MY-5 | P0 | No Cancel button on Approved/Rejected/Cancelled | Button absent |
| E2E-MY-6 | P0 | Request decided in another tab, then cancel with stale page | Error message, page reloads to current state (409) |
| E2E-MY-7 | P0 | HR cancels Approved leave with reason | Days refunded once; employee and manager notified; reason required; Keep is default |
| E2E-MY-8 | P0 | Deputy tries to cancel Approved leave | No button; API refused |
| E2E-MY-9 | P1 | Sick request viewed by owner vs. approver after approval | Owner sees Sick; approver sees "Off" |

## 5. Approvals (R17-R20, R22)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-APR-1 | P0 | Manager sees only direct reports' Pending items, with requester name | Other teams' items absent |
| E2E-APR-2 | P0 | Approve | Status Approved; employee emailed; item shows outcome |
| E2E-APR-3 | P0 | Reject without reason / 501 chars | Field error, focus on the field; nothing changes |
| E2E-APR-4 | P0 | Reject with reason | Rejected; days released; employee sees the reason |
| E2E-APR-5 | P0 | Two approvers/tabs decide the same request | Second gets "already decided" (409) |
| E2E-APR-6 | P0 | Approve/reject from request detail page | Same behaviour as list |
| E2E-APR-7 | P0 | Manager of another team opens approve/reject URLs via API | 403, denial audited |
| E2E-APR-8 | P0 | Plain employee opens Approvals | Link absent; direct URL shows no data (403) |
| E2E-APR-9 | P0 | Manager's own request is not in their own list; HR cannot approve own | Absent |
| E2E-APR-10 | P0 | HR admin who entered a request for someone cannot decide it | Absent from their list; other HR can |
| E2E-APR-11 | P0 | Manager request goes to HR queue; HR approves | Works; both HR admins see it |
| E2E-APR-12 | P0 | HR admin's request goes to deputy only | Deputy decides; other HR cannot |
| E2E-APR-13 | P0 | "On behalf of" tab: manager B decides for manager A's report | Audited with acting-for; direct manager A emailed; not on the default list |
| E2E-APR-14 | P1 | Cover list excludes the actor's own reports and own requests | Correct |
| E2E-APR-15 | P0 | Sick type visible while deciding, "Off" after | Matches the privacy matrix (section 8) |
| E2E-APR-16 | P1 | Approver with deactivated manager | Item reachable via cover or HR |

## 6. HR: employees, teams, deputy (R4, R9, R23, R36)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-HREMP-1 | P0 | Non-HR cannot open HR screens | Hidden in nav; direct URL denied |
| E2E-HREMP-2 | P0 | Create employee (valid) | Invite email queued; no link in HR response/UI |
| E2E-HREMP-3 | P0 | Create with a non-company email | Refused |
| E2E-HREMP-4 | P0 | Joiner starting 1 Jul | Pro-rated Annual 6.0, Sick 3.5; start 15 Jul counts July, 16 Jul does not |
| E2E-HREMP-5 | P0 | Assign manager creating a loop (A->B then B->A, A->B->C->A) | Refused |
| E2E-HREMP-6 | P1 | Edit name/role/team; inactive manager cannot be selected | Saved; audited |
| E2E-HREMP-7 | P0 | Deactivate employee | Cannot sign in; Pending requests handled per R4; audited |
| E2E-HREMP-8 | P1 | Teams: create, rename, assign manager | Reflected on calendar team filter |
| E2E-HREMP-9 | P0 | Settings: assign deputy; HR admin leave then routes to deputy | Routing changes; deputy cannot see HR-only screens |
| E2E-HREMP-10 | P1 | Deputy deactivated | Open deputy-queue items stay decidable by the next deputy |

## 7. HR: balances (R24)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-HRBAL-1 | P0 | List shows all active employees with balances | Searchable; correct year |
| E2E-HRBAL-2 | P0 | Enter opening balance: Review, then confirm | Summary step before save; saved entry in ledger with HR and time; no edit/delete |
| E2E-HRBAL-3 | P0 | Second opening for same type/year | 409 message |
| E2E-HRBAL-4 | P0 | Carry-over: 6 accepted, 6.5 refused, expiry date required | Matches cap; stacking with rollover refused |
| E2E-HRBAL-5 | P0 | Adjustment needs reason; may reference original entry | Original stays; new entry appended |
| E2E-HRBAL-6 | P0 | Adjustment that leaves a negative balance | Warning on the confirm step |
| E2E-HRBAL-7 | P1 | Leave-year picker (previous/current/next) | Entry saved in the chosen year |
| E2E-HRBAL-8 | P1 | Days not in 0.5 steps, out of range | Field error |
| E2E-HRBAL-9 | P1 | Launch list / print view | Lists employees without opening balance |
| E2E-HRBAL-10 | P0 | Non-HR sees nothing | Denied |

## 8. HR: holidays (R11)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-HOL-1 | P0 | Year list shows seeded holidays for 2026/2027 | Dates match Appendix A (also the A-19 verification checklist) |
| E2E-HOL-2 | P0 | Add holiday on a weekday with existing leave | "N requests affected" shown before saving |
| E2E-HOL-3 | P0 | Edit/delete holiday | Existing requests' `working_days` unchanged; new requests use new calendar; audited |
| E2E-HOL-4 | P1 | Holiday on a weekend | Accepted, no impact |
| E2E-HOL-5 | P0 | Non-HR denied | Hidden and denied |

## 9. HR: All leave (R25) and Team calendar (R27, P2)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-ALL-1 | P0 | HR sees all approved leave; filters by month, team, employee, type | Counts correct; Sick shown to HR |
| E2E-ALL-2 | P0 | Non-HR denied | Hidden and denied |
| E2E-CAL-1 | P0 | Employee sees own team's leave for a month | Others' Sick shown as "Off", identical for Pending and Approved |
| E2E-CAL-2 | P0 | Other teams' leave not visible to non-HR | Absent |
| E2E-CAL-3 | P1 | HR team filter and all-teams view | Works; Sick type visible to HR |
| E2E-CAL-4 | P1 | Month navigation, invalid year in URL (e.g. 0000) | Handled without a server error |
| E2E-CAL-5 | P1 | Public holidays and weekends marked | Visible |

## 10. HR: Monthly report (R28, P2)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-REP-1 | P0 | Month picker, preview | Days taken per employee; balances as at month end |
| E2E-REP-2 | P0 | Export Excel and CSV | File downloads; marked confidential; audited |
| E2E-REP-3 | P0 | Names/notes beginning `= + - @` or tab | Escaped in the file (no formula runs) |
| E2E-REP-4 | P0 | Sick type absent from the export | No Sick type, notes or reasons |
| E2E-REP-5 | P0 | Non-HR and deputy denied | Hidden and denied |

## 11. Notifications and email (R26, R35)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-NOT-1 | P0 | Submit, approve, reject, cancel each queue the right email to the right person | Recipients match routing; one per event |
| E2E-NOT-2 | P0 | Email content for a Sick request | No Sick type, note or reason; rejection reason only to the employee |
| E2E-NOT-3 | P1 | Failed email appears in HR Settings and can be retried | Retry succeeds; row clears |
| E2E-NOT-4 | P1 | In-app notifications API: unread count, mark read | **Blocked: bell UI not built.** API-level only for now |

## 12. Authorization and security (R29, R30; run in the browser context)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-SEC-1 | P0 | Every HR route, as employee / manager / deputy | 403 and nav hidden |
| E2E-SEC-2 | P0 | State-changing call without CSRF header or from another origin | Rejected |
| E2E-SEC-3 | P0 | Unknown fields in request body | Refused (strict schema) |
| E2E-SEC-4 | P0 | Errors use the standard envelope; no stack trace in production config | Matches spec 6.1 |
| E2E-SEC-5 | P0 | Security headers present; `/docs` absent outside dev | Present / 404 |
| E2E-SEC-6 | P1 | Audit entries for approve, reject, cancel, HR edits, denials | Present with actor; no Sick type, notes, reasons, tokens |

## 13. Accessibility and mobile (R31) - run on every screen

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-A11Y-1 | P0 | At 360 px: no horizontal scroll on each screen | Pass |
| E2E-A11Y-2 | P0 | Interactive targets at least 44 x 44 px | Pass |
| E2E-A11Y-3 | P0 | axe (WCAG 2.1 AA) on each screen and each open dialog | No violations |
| E2E-A11Y-4 | P0 | Every field labelled; first error receives focus; error summary | Pass |
| E2E-A11Y-5 | P0 | Destructive dialogs: focus on "Keep", Escape keeps, focus trapped, page behind inert, focus returns | Pass |
| E2E-A11Y-6 | P1 | Keyboard-only run of the request flow | Completable |
| E2E-A11Y-7 | P1 | 200% zoom on request form and approvals | No loss of content |
| E2E-A11Y-8 | P1 | Dates read as "Mon 2 Nov 2026" everywhere | No ambiguous formats |

## 14. Platform (R32, R33, R34)

| ID | Pri | Case | Expected |
|---|---|---|---|
| E2E-PLAT-1 | P0 | SPA served at `/`; deep link refresh works; unknown `/api/v9/...` returns the 404 envelope | Pass |
| E2E-PLAT-2 | P1 | `/healthz` OK | Pass |
| E2E-PLAT-3 | P1 | Page load and list render within budget on a seeded ~250-user data set | Within R32 limits |

## Coverage summary

About 150 cases: P0 about 95. Cases that need the backend clock (rollover on 1 Jan, `expire_carry`, 23:59 notice edge, year-end spans) stay in pytest; the browser tests only check what the screen shows after those states exist in seed data.

## Implementation status (local run, desktop 1280 and 1024)

Run: see `e2e/README` section below. 89 tests per desktop width, all passing (178 total).

| Spec file | Covers |
|---|---|
| `features/requests.spec.ts` | REQ-1,2,4,6,7,8,10,11,13,16,18,19,20; DASH-1,2,5; MY-1..4 |
| `features/approvals.spec.ts` | APR-1..8, 10..13, 15 |
| `features/hr.spec.ts` | HREMP-1,2,3,7,9; HRBAL-1..4,6; HOL-1..3; ALL-1; REP-2,3; SEC-1 |
| `features/auth.spec.ts` | AUTH-1..10 (API level, no screens), SEC-2, PLAT-1 |
| `features/calendar.spec.ts` | CAL-1 (page loads), CAL-4 |
| `features/responsive.spec.ts` | A11Y-1, A11Y-3, A11Y-5 on 12 screens |

Not yet covered: REQ-3/5/9/12/14/15/17, DASH-3/4/6/7/8, MY-5..9, APR-9/14/16, HREMP-4..6/8/10, HRBAL-5/7..10, HOL-4/5, CAL-2/3/5 (needs leave on the calendar), ALL-2, REP-5, NOT-1..3, SEC-3..6, A11Y-2/4/6/7/8.
Blocked (not built): sign-in/set-password/reset/sign-out screens, notification bell, HR audit log, HR "Enter leave" form.

### Run locally

```bash
docker exec leavedesk-pg psql -U postgres -c "create database leavedesk_e2e"
export E2E_DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5434/leavedesk_e2e
DATABASE_URL=$E2E_DATABASE_URL APP_DB_ROLE=leavedesk_app SET_ROLE_ON_CONNECT=true EMAIL_BACKEND=mock \
  COOKIE_SECURE=false COMPANY_TZ=Asia/Ho_Chi_Minh APP_BASE_URL=http://localhost:8000 ENVIRONMENT=dev \
  uv run alembic upgrade head
(cd frontend && npm run build)
# same env as above, then:
uv run uvicorn app.main:create_app --factory --port 8000 &
cd frontend && PLAYWRIGHT_CHROMIUM_PATH=/usr/bin/google-chrome npx playwright test --project=desktop-1280 --project=desktop-1024
```
The database name must end in `_e2e`; `scripts/e2e_db.py` refuses anything else.
