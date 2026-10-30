# Spec: LeaveDesk, internal leave management tool

Source of truth: `specs/001-leave-management-tool/intent.md`. Status: **Draft for review**. Date: 2026-10-28. Go-live: 2026-11-01.

## 0. How this spec was produced

- The intent file was read in full. Nothing in it was invented. Anything not in the intent is marked **[Assumption]** and also listed in section 11 or 12.
- Each requirement has a tag: **[P1]** is needed on 1 Nov, **[P2]** ships about two weeks later (calendar and report).

## 1. Scope summary

| | Phase 1 (1 Nov) | Phase 2 (Mon 16 Nov 2026) |
|---|---|---|
| Staff | Request, cancel while Pending, view balance and own requests | Team calendar |
| Managers | Approve or reject (reason required), cover for an absent manager | |
| HR | Employees, teams, managers, holidays, starting balances; see all approved leave; cancel Approved; approve managers' requests | All-team calendar; monthly Excel/CSV report |
| System | Email notifications, password login | |
| Out of scope | Google SSO, Slack/Teams, history import, balance CSV import, other leave types, non-Vietnamese holidays, Saturday/shift patterns | |

## 2. Tech stack

Chosen for the cost ceiling (under $5/month), low maintenance, and a one-developer team with four days to launch. **Revised:** the UI is a React SPA (Vite) and the whole app is deployed to FastAPI Cloud as one full-stack service (same domain, so no CORS). See C-16 for the cost and database risks this introduces.

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.14, FastAPI, vertical modules (router, service, repository, models, schemas, dependencies) | Matches the pattern already in this repo (`add-endpoint` skill). |
| Database | **PostgreSQL on Supabase** (managed). FastAPI connects with SQLAlchemy 2 and Alembic through the Supabase connection pooler (the IPv4-compatible pooled connection string, kept as a platform secret). **Row Level Security is enabled with no policies on every table**, and Supabase's auto-generated REST/GraphQL access and Supabase Auth are not used, so the database can be reached only through the FastAPI API. Supabase is used as a hosted PostgreSQL only. **Decided 2026-10-28: free tier, Singapore region.** The free tier can pause an inactive project, so a daily keep-alive request (a scheduled CI job calling `/healthz`, which runs a trivial query) is required, and the nightly `pg_dump` below is the real backup. | Balances and leave data must survive redeploys, and the app instance filesystem cannot be relied on. RLS with no policies stops anyone with the public project URL and anon key from reading HR data. |
| UI | React 18 + TypeScript, built with Vite. React Router, TanStack Query for server state, React Hook Form + Zod for forms and validation, mobile-first CSS (CSS modules or Tailwind). The build output (`frontend/dist`) is served by FastAPI at `/`, with the JSON API under `/api/v1` on the same origin. | Same-origin deployment keeps cookies simple and removes CORS. Zod schemas mirror the API schemas, and the server still validates everything (R29). |
| Auth | **Built in the app (no external identity provider).** Email + password, hashed with Argon2id. FastAPI issues a random session token stored hashed in the database and sent as a `HttpOnly; Secure; SameSite=Lax` cookie, so no token is readable by React code. The SPA is same-origin, so the cookie is sent automatically. CSRF protection: a token returned by `GET /me`, sent by the SPA in an `X-CSRF-Token` header on every state-changing call, plus an `Origin` check. Invite and reset links are one-time tokens emailed through SendGrid. A `user_identity` table keeps the provider separate, so Google SSO can be added later without a schema change. | Intent: password now, Google SSO later. HttpOnly cookies suit a same-origin React SPA and avoid token theft through XSS. |
| Email | **Twilio SendGrid** (API, key held as a platform secret) behind an `EmailSender` interface. A `MockEmailSender` (`EMAIL_BACKEND=mock`) is used only in local development and automated tests. The sender domain (`@asnet.com.vn` or a subdomain) needs SPF, DKIM and DMARC records. | Intent requires email notifications and invites. The interface keeps tests offline and the provider replaceable. **[Assumption: "Twilio" means SendGrid; confirm plan and free-tier limits, Q14]** |
| Hosting | **FastAPI Cloud**, one service deployed with `fastapi deploy`. CI builds the Vite bundle first and deploys it together with the backend. TLS and the CDN for static assets are provided by the platform. Environments: staging and production. Secrets (database URL, SMTP credentials, session key) are set as platform environment variables, never committed. | Fits the Python stack and the same-domain full-stack model. Target ≤ $5/month **[Assumption: plan price, database price and limits to confirm, see C-16 and Q5]**. |
| Backups | Supabase backups for the plan chosen **[verify: point-in-time recovery and daily-backup retention depend on the plan]**. In addition, a nightly `pg_dump` from CI to private object storage, 30-day retention, and a documented restore drill. | Protects the one thing that can't be recreated (balances). |
| Excel export (P2) | CSV plus `.xlsx` via `openpyxl` | Intent: Excel/CSV. |
| Tests | Backend: pytest, httpx, `ruff`, `mypy`. Frontend: Vitest + React Testing Library, `eslint`, `tsc --noEmit`. End to end: Playwright against staging for the main flows, as each role. | |

## 3. Roles and permissions

| Capability | Employee | Manager | HR |
|---|---|---|---|
| Request leave, view own balance and requests | Yes | Yes (own requests go to HR) | Yes (**see C-6**) |
| Cancel own request | Pending only | Pending only | Pending only |
| Approve or reject | No | Direct reports; any other manager if the direct manager is away | Managers' requests |
| Cancel an Approved request | No | No | Yes (refunds days) |
| See leave of others | No (P2: own team, sick shown as "Off") | Own team (P2) | All approved leave (P1), all teams (P2) |
| Manage employees, teams, holidays, balances | No | No | Yes |
| Export report (P2) | No | No | Yes |

The deputy HR admin (R36) is an employee or manager with `is_hr_deputy`; they gain only the HR-approver rights (decide managers' and HR's requests) and none of the HR column's administration rights.

Authorization is checked in the service layer on every request. Hiding a button is not an access control.

## 4. Requirements

Format: **R#** [phase] statement, then acceptance criteria. Every R has at least one Given/When/Then.

### 4.1 Authentication and accounts

**R1 [P1] Login with company email and password.**
- Given an active user with a valid password, when they sign in on the React login page with `name@asnet.com.vn`, then the API starts a session (cookie) and they land on the Dashboard.
- Given an email that does not end in `@asnet.com.vn`, when HR creates or invites the account, then it is rejected with an error message.
- Given a wrong email or wrong password, when sign-in is submitted, then the same generic message "Email or password is incorrect" appears. It must not reveal which part is wrong, and the response time does not differ between unknown emails and wrong passwords.

**R2 [P1] Account protection.**
- Given 5 failed sign-ins for one email within 15 minutes, when a 6th is attempted, then it is refused for 15 minutes, whatever the password. The attempt is logged. A per-IP limit also applies.
- Given a new password, when it is set, then it must be at least 12 characters and not be a common password. It is stored only as an Argon2id hash.
- Given 8 hours of inactivity (and a 24-hour maximum session age), when the user acts, then they are signed out. All sessions are invalidated on password change.
- Given the SPA receives a 401 from any call, when it happens, then it clears local state and shows the sign-in page, keeping the page the user was on so they return to it.

**R3 [P1] Invite and reset by email.**
- Given HR creates an employee, when the record is saved, then a one-time invite link (valid 48 hours, single use) is emailed so the employee sets their own password on the SPA's "Set password" page. HR never sees or sets a password or a link.
- Given "Forgot password", when any email is submitted, then the same response is shown whether or not the account exists. If it exists, a one-time reset link (valid 1 hour) is emailed. Tokens are stored only as hashes.
- Given an expired or used link, when it is opened, then the SPA shows a clear message and a way to request a new one.

**R4 [P1] Deactivation.**
- Given HR deactivates an employee, when that person next makes a request, then it is refused and their sessions are deleted. Their history stays. Their Pending requests are cancelled and the manager is told.
- **[Assumption]** (A-11) Deactivating an HR admin, the deputy or yourself is refused (422) until HR rules are decided. Pending requests assigned *to* a deactivated manager are not rerouted. Approved future leave of the deactivated employee keeps its reservation. Pending requests are cancelled with the fixed reason "Account deactivated" (`cancelled_by` is the HR actor); the manager (or HR approvers) get `request_cancelled_on_deactivation`, with no type or note.

### 4.2 Leave types, balances and calendar of working days

**R5 [P1] Leave types and entitlements.**
- Given the leave year (1 Jan–31 Dec), when a full-year employee's balance is shown, then Annual = 12 days, Sick = 7 paid days, and Unpaid has no limit and no balance.
- Given Annual leave unused at year end, when the new year starts, then at most 6 days carry over (see R7).

**R6 [P1] Working-day calculation.**
- Given a request from Fri 6 Nov to Mon 9 Nov, when days are counted, then the result is 2.
- Given a range that includes a preloaded or HR-added public holiday on a weekday, when days are counted, then that day is excluded.
- Given a request that spans two leave years, when it is saved, then days are counted and deducted per leave year.
- Given a range with no working days (a weekend or a holiday only), when it is submitted, then it is rejected with "This range has no working days."

**R7 [P1] Carry-over and expiry.**
- Given an employee has 4 unused Annual days on 31 Dec 2026, when 1 Jan 2027 starts, then a carry-over entry of 4 days is created, expiring 31 Dec 2027.
- Given 9 unused days, when the year rolls over, then 6 are carried and 3 are lost.
- Given carried days and current-year days, when a request is approved, then carried days are used first.
- Given carried days that pass their expiry, when the balance is computed, then they no longer count. The expiry is recorded as an entry, not a silent overwrite.
- Re-carrying already-carried days is **not** allowed in v1 (**see Q4, a default pending confirmation**).

**R8 [P1] Sick leave does not carry over.**
- Given unused Sick days on 31 Dec, when the year rolls over, then none carry over.

**R9 [P1] New joiner pro-rating.**
- Given an employee who starts on 1 Jul (6 months remaining), when HR saves the start date, then Annual = 12 × 6/12 = 6.0 days and Sick = 7 × 6/12 = 3.5 days, rounded to the nearest 0.5 day.
- Given a result such as 3.25, when rounded, then it becomes 3.5 (half-up to the nearest 0.5).
- The method (remaining whole months, mid-month rule, and whether Sick is pro-rated) is **an assumption pending Q2**. HR can override with an audited manual adjustment.
- **[Assumption, A-8]** Edge cases as implemented: a start in the current year writes `prorata` entries (a January joiner gets the full 12.0 and 7.0; a start on 16 Dec or later has 0 months and writes nothing). A start in an earlier year writes the normal current-year `entitlement`. A start in a future year is refused with 422. The start date and email cannot be changed after create, so no ledger rewrite is needed. Rollover writes `entitlement` only when the start year is before the new year, so a joiner never gets both.

**R10 [P1] Balance display.**
- Given an employee, when they open the Dashboard, then they see per type: entitlement, carried-over (with its expiry date), used (Approved), reserved (Pending) and available.
- Available = entitlement + carried − used − reserved. **[Assumption: Pending requests reserve days]** (see C-10).
- Given the balance would go below zero, when an Annual or Sick request is submitted, then it is blocked with the shortfall stated. Unpaid is never blocked.

**R11 [P1] Public holidays.**
- Given first deployment, when the app starts, then Vietnamese public holidays for 2026 and 2027, including official compensatory days off, are preloaded **[Assumption: the list follows the government's annual decree; HR verifies it and edits as needed; Tet and Hung Kings dates are lunar]** (see Q6).
- Given HR adds, edits or deletes a holiday, when it is saved, then the change is audited, and HR sees the number of existing Pending or Approved requests it touches (see C-8).

### 4.3 Requesting leave

**R12 [P1] Create a request.**
- Given an active employee, when they pick type, start date, end date, and (for single days) Full / Morning / Afternoon, then a Pending request is created with the computed working days and an optional note.
- Given a single-day request, when a half day is chosen, then start and end carry the same part (`am` or `pm`). Given a multi-day request, then the first day may be `full` or `pm` (afternoon only) and the last day `full` or `am` (morning only); starting on `am` or ending on `pm` is refused (**decided, Q7**; A-22).
- Given any half day, when days are counted, then it counts as 0.5.

**R13 [P1] Validation and overlap.**
- Given an end date before the start date, when submitted, then it is refused with an inline message next to the field.
- Given the new range overlaps the employee's own Pending or Approved request (a morning and an afternoon half day on the same date do not overlap), when submitted, then it is refused and names the conflicting request. **[Assumption: not in the intent]**
- Given a start date in the past for Annual or Unpaid, when submitted, then it is refused. For Sick see R15.

**R14 [P1] Notice rules.**
- Given a single-day Annual or Unpaid request, when it starts in less than 1 day, then it is rejected.
- Given a request longer than one week (more than 5 working days, C-3), when it starts less than the notice period away, then a **warning** is shown to the employee and to the approver, and the request can still be submitted (**decided, Q1: 1 week, warning only**).
- Given a request of 2–5 working days, when submitted, then no notice rule applies, because the intent does not define one (**see C-3**).
- Notice is measured in calendar days from the submission time, in the company time zone (**see C-12**).
- **[Assumption, A-9]** "Less than 1 day" is the literal calendar-day difference between the start date and today (company time zone): starting today is blocked, starting tomorrow is allowed. A single half-day counts as a single day. "Less than the notice period" is fewer than 7 calendar days. Sick is exempt from both rules. Confirm with the product owner before launch.

**R15 [P1] Sick leave is exempt from notice.** **[Assumption; see C-4]**
- Given a Sick request that starts today or in the past, when submitted, then the notice rule is not applied. The employee may enter Sick leave up to 7 days in the past. For older dates only HR can enter it on the employee's behalf, with a reason, and it is audited (**decided, Q8**).
- **[Assumption, A-12]** HR entry (`POST /hr/requests`) skips the notice rule (and the past-date rule for Sick only), still applies overlap and balance, routes the request normally, never lets HR enter leave for themselves, and does not separately notify the employee. The reason is stored on the request and kept out of audit detail and emails.

**R16 [P1] Cancel own Pending request.**
- Given the employee's own Pending request, when they cancel it (after a confirmation step), then its status becomes Cancelled, reserved days are released, and the approver is notified.
- Given an Approved, Rejected or Cancelled request, when the employee tries to cancel it through the UI or the API, then the API returns 403 and the UI shows no cancel button.

### 4.4 Approval

**R17 [P1] Routing.**
- Given a request from an employee with a direct manager, when it is created, then it is assigned to that manager and the manager is emailed.
- Given a request from a manager, when it is created, then it is assigned to HR and HR is emailed.
- Given a request that has no route, when it is submitted, then it is refused with a clear `422` and nothing is saved: an employee with no active direct manager (`NO_APPROVER`), a manager when no HR approver other than them exists (`NO_APPROVER`), and an HR admin's own request until the deputy route ships (`ROUTE_UNAVAILABLE`, plan 17). **[Assumption: A-10, not in the intent]**
- Given a manager's request, then "HR is emailed" means every active HR approver (HR admin or deputy) except the requester, each emailed and notified once. **[Assumption: A-14]**
- Given a person's own request, when they try to approve it, then it is refused, whatever their role.

**R18 [P1] Approve.**
- Given a Pending request assigned to a manager, when the direct manager approves, then status becomes Approved, days move from reserved to used, and the employee is emailed.
- Given a Pending request, when two approvers act at the same moment, then exactly one succeeds and the other sees "This request was already decided." (optimistic locking).

**R19 [P1] Reject with reason.**
- Given a Pending request, when the manager rejects without a reason (or with only whitespace), then the action is refused with an inline error.
- Given a reason of 1–500 characters, when the manager rejects, then status becomes Rejected, reserved days are released, and the employee is emailed with the reason.

**R20 [P1] Cover for an absent manager.**
- Given a direct manager is away, when another manager opens "Approve on behalf", then they can see and decide that manager's Pending requests.
- Given any decision made on behalf, when it is saved, then the audit log records both the actual approver and the direct manager, and the direct manager is emailed.
- How "away" is determined (**decided, Q9**): the system does not track absence. Any manager can cover an absent manager through the "On behalf of" tab, and the audit entry and the email to the direct manager are the only controls (see C-5). An "away" flag with dates is a possible later hardening step, not part of v1.

**R21 [P1] HR cancels Approved leave.**
- Given an Approved request, when HR cancels it with a reason, then status becomes Cancelled, used days are refunded, and the employee and manager are emailed.
- Given the same request is cancelled twice, when the second call arrives, then the days are refunded only once.

**R22 [P1] Approver cannot act on another team's request through the API.**
- Given a manager who is neither the direct manager nor using cover, when they call the approve endpoint for a request outside their reports, then the API returns 403 (employees/HR) and the attempt is logged. Cover mode is defined in R20.

### 4.5 HR administration

**R23 [P1] Employees, teams and managers.**
- Given HR, when they create or edit an employee (name, email, team, direct manager, start date, active flag), then the change is saved and audited.
- Given a manager reference that would create a loop (A manages B manages A), when saved, then it is refused.
- Given anyone other than HR, when they call these endpoints, then the API returns 403.
- **[Assumption]** The manager reference may be any other active employee (not only role `manager`), which is what makes A→B→C→A loops possible and testable. Create and edit do not change `is_active`: deactivation is endpoint 19 (R4). A role change is audited as `employee.role_change` (R30); its effect on existing Pending requests is not specified yet.

**R24 [P1] Starting balances by hand.**
- Given HR, when they enter an employee's opening Annual days, carried days with their expiry date, and Sick days, then the entries are saved as ledger entries with the entering user and time.
- Given an entered value outside 0–40 days, when saved, then it is refused. Before saving, HR sees a confirmation summary (**the safeguard for "no balance corrections", see C-9**).
- Given an entry already saved, when HR changes it, then the original stays in the ledger and a new adjustment entry is added with a required reason. Entries are never overwritten.
- **[Assumption] (A-18, pending product owner):** an `adjustment` is signed and bounded −40..40 in 0.5 steps; opening Sick may be entered (0–40); manual `carry_over` is Annual only and its `expires_on` must fall in the entry's leave year; every manual `days` is a multiple of 0.5. The confirmation step is enforced in the UI only: the API offers a preview (#25) but does not require a token before #26.

**R25 [P1] HR sees all approved leave.**
- Given HR, when they open "All leave", then they see all Approved leave (and can filter by Pending, date range, employee, team and type), with real leave types.
- **[Assumption]** `from`/`to` match any request overlapping the range; results are ordered by start date then id, 50 per page (max 200), status defaults to Approved and takes one value at a time. The deputy gets 403.

### 4.6 Notifications

**R26 [P1] Email notifications.**
- Given the events: request created, approved, rejected, cancelled by employee, cancelled by HR, approved on behalf, rejected on behalf (both to the direct manager), invite, password reset, when each occurs, then the right recipient gets one email.
- Given an email is sent, then it contains the date range and a link, but **not** the leave type when the type is Sick, and never the note. Rejection reasons go to the employee only. (hr-privacy; see C-2)
- Given `EMAIL_BACKEND=mock` (development and tests only), when an event occurs, then the rendered email is stored in `email_outbox` with status `mocked` and nothing is sent.
- Given SendGrid is down or rejects a message, when an event occurs, then the email stays in the outbox and is retried with back-off. The request is not lost, and HR can see failed sends.
- Given `EMAIL_BACKEND=mock` in production, when the app starts, then it refuses to start.

**R35 [P1] In-app notifications.** **[Assumption: not in the intent, which says email only; see C-17]**
- Given any R26 event, when it occurs, then a notification is also created for the recipient and shown in a bell menu with an unread count.
- Given a notification, when the recipient opens it, then it is marked read and links to the request or page.
- Given a user calls the notifications API for someone else's notifications, then it returns 403. Notification text follows the same privacy rules as email (no Sick type, no notes).
- Given a new employee who has no account yet, then the invite is delivered by email only, because the person cannot sign in (R3).

**R36 [P1] Deputy HR admin.** (decided, Q12)
- Given HR assigns the deputy HR role to one named active employee, when it is saved, then the change is audited. At most one deputy exists at a time.
- Given an HR user submits their own leave, when it is created, then it is assigned to the deputy, and the HR user cannot approve it.
- Given HR is away, when the deputy opens Approvals, then they can decide managers' requests, and the audit log records the deputy as actor.
- Given the deputy, then they have no access to employee, team, holiday or balance administration, or to exports, unless HR grants it (**decided: approval and cover only**).

### 4.7 Calendar (P2)

**R27 [P2] Team calendar.**
- Given an employee, when they open the calendar, then they see only their own team's Approved and Pending leave for the month, with Pending visibly distinct (by label as well as colour).
- Given any viewer who is not HR and not the leave owner, when the entry is Sick leave, then it is shown as "Off", with no type, no note, and no pending/approved distinction that would reveal the type (see C-2).
- Given the viewer is HR, when the calendar opens, then they can see all teams and the real leave type.
- Given a request from another team, when the API is called by an employee for another team, then it returns 403.

### 4.8 Monthly report (P2)

**R28 [P2] Monthly export.**
- Given HR selects a month, when they click Export, then a file (Excel or CSV) is produced in under 10 minutes of HR effort, with: days taken per employee per type, remaining balances, and who was off and when.
- Given any cell starting with `=`, `+`, `-`, `@` or tab, when it is written, then it is prefixed so a spreadsheet cannot run it as a formula.
- Given a non-HR user calls the export endpoint, then the API returns 403. Every export is audited (who, month, time).

### 4.9 Non-functional

**R29 [P1] API security baseline (every endpoint).**
- Given any endpoint other than login, invite and reset, when it is called without a valid session, then it returns 401.
- Given any input, when it is received, then it is validated against a schema (types, lengths, enum values, dates). Unknown fields are refused. Queries are parameterised.
- Given a request without a valid session cookie, then it returns 401. Given a state-changing request without a valid CSRF token or with a foreign `Origin`, then it returns 403. The SPA must not render untrusted HTML, and a strict CSP limits script sources.
- Given any response, then it carries security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy`, HSTS), and in production errors do not leak stack traces (`error.stack` is allowed only when `ENVIRONMENT` is not `production`, §6.1).

**R30 [P1] Audit log.**
- Given any create, approve, reject, cancel, balance change, holiday change, employee change, login failure, role change or export, when it happens, then an append-only record is written with actor, action, target, time, and before/after values where relevant.
- Given the log, then it never stores passwords, tokens, notes, rejection reasons or leave types of Sick leave in free-text fields. Application logs follow the same rule.

**R31 [P1] Mobile and accessibility (UX standard).**
- Given a 360 px-wide phone, when any P1 screen is used, then no horizontal scrolling is needed, touch targets are at least 44 px, and the request can be made and approved in a phone browser.
- Given a keyboard or a screen reader, when forms are used, then every field has a visible label, errors are announced and linked to their fields, and colour is never the only signal. Contrast is at least WCAG 2.1 AA.
- Given a date is shown, then it is unambiguous, e.g. "Mon 2 Nov 2026". Date pickers accept and show the same format.
- Given a form error, when it is submitted, then the form keeps what the user typed, says what is wrong and how to fix it, and moves focus to the first error.
- Given a destructive action (cancel, reject, deactivate, delete holiday), when it is clicked, then a confirmation names exactly what will happen, and the default focus is on "Keep".

**R32 [P1] Performance and capacity.**
- Given 250 users and 150 requests a month, when pages load, then the 95th percentile server time is under 500 ms on the target host.

**R33 [P1] Backup and restore.**
- Given the nightly backup, when a restore drill is run, then the database is restored in under 30 minutes, with a documented procedure.

**R34 [P1] Data retention.** **[Assumption; see Q10]**
- Given a deactivated employee, then their leave history is kept for 7 years **[Assumption: confirm with legal/HR]**, accessible only to HR.

## 5. Data model

PostgreSQL (Supabase), managed with Alembic. Conventions:

- `id uuid` primary key (`gen_random_uuid()`); `created_at` and `updated_at` are `timestamptz` in UTC; dates are `date`. All business-day decisions (today, notice, leave year, holidays) use the company time zone `COMPANY_TZ` (`Asia/Ho_Chi_Minh`).
- Day quantities are `numeric(4,1)` with `CHECK (days * 2 = round(days * 2))` (0.5 steps). Enums are `text` with `CHECK` lists.
- Every table has Row Level Security enabled with no policies (C-18). The app's database role has no `UPDATE`, `DELETE` or `TRUNCATE` on the append-only tables (`balance_entry`, `audit_log`).
- Role terms used in this spec: **HR admin** = `employee.role = 'hr'`; **deputy** = the one active employee with `is_hr_deputy = true` (R36); **HR approver** = HR admin or deputy.

### 5.1 Tables

| Table | Key columns | Constraints and notes |
|---|---|---|
| `employee` | name, email (`citext`, unique), role (`employee`/`manager`/`hr`), is_hr_deputy (bool, default false), team_id → team, manager_id → employee, start_date, end_date, is_active, deactivated_at | `CHECK (email LIKE '%@asnet.com.vn')` (R1). `CHECK (manager_id <> id)`; loops (A→B→A) are refused by a recursive check in the same transaction (R23). `manager_id` is null for managers and HR (they route to HR, R17). Partial unique index on `(is_hr_deputy) WHERE is_hr_deputy AND is_active` gives at most one deputy; `CHECK (NOT (is_hr_deputy AND role = 'hr'))`. The deputy keeps their own role and has no admin rights (R36). |
| `user_identity` | employee_id, provider (`password`/`google`), password_hash (null until the invite is accepted, or for `google`), provider_subject (null for `password`), password_changed_at, last_login_at | Unique `(employee_id, provider)` and `(provider, provider_subject)`. Argon2id hashes only. Provider is separate so Google SSO needs no schema change. |
| `session` | employee_id, token_hash (unique), csrf_token_hash, created_at, last_seen_at, expires_at | Only hashes stored. Expires at the earlier of `last_seen_at + 8h` and `created_at + 24h` (R2). Deleted on password change and deactivation (R4). Expired rows purged daily. |
| `one_time_token` | employee_id, purpose (`invite`/`reset`), token_hash (unique), expires_at, used_at | Invite 48 h, reset 1 h, single use. Issuing a new token sets `used_at` on the previous active one for the same purpose (R3). |
| `login_attempt` | email_hash, ip, at, success | Indexes `(email_hash, at)` and `(ip, at)` for lockout and per-IP limits (R2). Purged after 30 days. |
| `team` | name (unique), manager_id → employee | |
| `leave_type` | code (pk: `annual`/`sick`/`unpaid`), annual_allowance, carry_cap, carries_over, is_limited, allow_backdate_days, notice_exempt, is_sensitive | Seed: annual 12 / cap 6 / carries / limited / backdate 0 / notice applies; sick 7 / cap 0 / no carry / limited / backdate 7 / notice exempt / sensitive; unpaid null / 0 / no carry / not limited / backdate 0. `is_sensitive` drives the "Off" masking in §8. |
| `balance_entry` | employee_id, leave_type_code, leave_year, kind (`opening`/`entitlement`/`prorata`/`carry_over`/`expiry`/`adjustment`), days (signed), expires_on (only `carry_over`), reason, source (`manual`/`system`), idempotency_key (unique, nullable), corrects_entry_id → balance_entry, created_by | Append-only ledger (R24). `reason` is required for `adjustment` (`CHECK`). Manual `opening` and `carry_over` entries must be 0–40. `entitlement` rows (12 annual, 7 sick) and rollover `carry_over`/`expiry` rows are written by the system with an `idempotency_key` such as `rollover:2027:<employee_id>`, so a job that runs twice cannot double-credit. No entries exist for `unpaid`. |
| `leave_request` | employee_id, leave_type_code, start_date, start_part (`full`/`pm`/`am`), end_date, end_part, working_days (snapshot), note, status (`pending`/`approved`/`rejected`/`cancelled`), queue (`manager`/`hr`/`deputy`), assigned_to → employee, submitted_at, notice_warning (bool), entered_by → employee, entry_reason, decided_by, decided_on_behalf_of → employee, decided_at, decision_reason, cancelled_by, cancelled_at, cancel_reason, version | See 5.2 for the checks. `note` is optional, max 500 characters, and is never copied into email, notification, audit or log text. `queue = 'manager'` → `assigned_to` is the direct manager. `queue = 'hr'` (a manager's request) → `assigned_to` is null and any HR approver other than the requester may decide. `queue = 'deputy'` (an HR admin's own request) → `assigned_to` is the deputy (R36). `entered_by`/`entry_reason` are set when HR enters leave for someone (R15). `version` is for optimistic locking (R18). |
| `leave_request_day` | request_id → leave_request, employee_id, leave_date, slot (`am`/`pm`), leave_year, is_active | Primary key `(request_id, leave_date, slot)`. One row per **working half day** (a full day is two rows, `am` and `pm`; weekends and holidays are never stored). `is_active` is true while the parent is `pending` or `approved` and is set false in the same transaction on reject or cancel. **Partial unique index `(employee_id, leave_date, slot) WHERE is_active`** makes overlap (R13) impossible even under concurrent submits, while a morning and an afternoon half day on one date do not clash. `leave_year` lets a request that spans two years deduct per year (R6). |
| `public_holiday` | holiday_date (unique), name, source (`seed`/`manual`), created_by | Edits never rewrite `working_days` or `leave_request_day` (C-8). Affected requests are found by query (R11): Pending or Approved requests whose date range covers the date, counted for weekday dates only (a weekend holiday changes nothing). The range, not the day rows, is used so deleting a holiday also finds requests that skipped it. A move counts the old and the new date. Seeded by migration 0005 from Appendix A. |
| `audit_log` | actor_id, acting_for_id (cover manager or deputy: the person the actor stood in for), action, target_type, target_id, detail (`jsonb`), ip, at | Append-only (R30). `detail` holds ids and before/after values of non-sensitive fields only: never notes, rejection reasons, tokens, or the type of Sick leave in free text. Kept 7 years (R34). |
| `email_outbox` | recipient_employee_id, to_address, template, payload (`jsonb`), subject and body (rendered at emit time, privacy-checked; **[Assumption]** invite/reset bodies hold a one-time link), dedupe_key (unique), status (`pending`/`sent`/`failed`/`mocked`), attempts, next_try_at, sent_at, last_error | Written in the same transaction as the event (outbox pattern), so a request is never lost if SendGrid is down (R26). `payload` is privacy-filtered (no Sick type, no note). `last_error` holds the provider status code only. Back-off 1 min, 5 min, 30 min, 2 h, 12 h; after 5 attempts → `failed`, visible to HR. **[Assumption]** The 5th failure ends retries, so the 12 h step is unused (confirm 5 attempts vs 5 retries). `notification` also has a unique `dedupe_key`; rows are never deleted by the app role. |
| `notification` | employee_id, kind, title, body, link, request_id, read_at | Privacy-filtered like email (R35). Own rows only. |

### 5.2 Checks on `leave_request`

- `end_date >= start_date`.
- If `start_date = end_date`: `start_part = end_part` (`full`, `am` or `pm`). If `start_date < end_date`: `start_part IN ('full','pm')` and `end_part IN ('full','am')` (Q7, R12).
- `status = 'rejected'` → `decision_reason` is not blank and at most 500 characters (R19).
- `status = 'cancelled' AND cancelled_by <> employee_id` → `cancel_reason` is not null (R21).
- `decided_by <> employee_id` and `decided_on_behalf_of <> employee_id` (no one approves their own request, R17).
- `working_days > 0` (R6).

### 5.3 Indexes

`leave_request(assigned_to, status)`, `leave_request(queue, status)`, `leave_request(employee_id, start_date)`, `leave_request(status, start_date)` (HR "All leave", report); `leave_request_day(leave_date, employee_id) WHERE is_active` (calendar, report); `leave_request_day(employee_id, leave_year)` (balances); `balance_entry(employee_id, leave_year)`; `audit_log(at)`, `audit_log(target_type, target_id)`, `audit_log(actor_id, at)`; `email_outbox(status, next_try_at)`; `notification(employee_id, read_at, created_at)`.

### 5.4 Derived values (nothing mutable is stored)

For one employee, leave type and `leave_year`:

- **Entitlement** = sum of `opening`, `entitlement`, `prorata` and `adjustment` entries.
- **Carried** = sum of `carry_over` entries; a carried block stops counting after its `expires_on`.
- **Used** = 0.5 × active `leave_request_day` rows of `approved` requests. **Reserved** = the same for `pending` requests (C-10).
- **Consumption order:** days are taken from the carried block first (while it is unexpired on the leave date), then from entitlement (R7).
- **Available** = entitlement + carried (unexpired) − used − reserved (R10). Unpaid has no balance and is never blocked.
- One pure function `compute_balance(entries, days, today)` implements all of this and is the only place the rules live (tests: §10). The balance is therefore correct even if the nightly expiry job lags, because expiry is also computed from `expires_on`.
- **Unused for rollover (A-7)** = entitlement entries of the year minus the days taken from entitlement (carried days are consumed first and never count), with **Pending reservations counted as taken** and a floor of 0. Carry = `min(6, unused)`, so a carried block can never be carried again (R7). `expiry` entries are a record only: `compute_balance` ignores them and derives expiry from `expires_on`. **[Assumption: a Pending request that is later rejected does not restore days to a rollover already written; HR adds an `adjustment`.]**
- **Refund** (R21) is just the status change `approved → cancelled` with `is_active = false`; no ledger row is needed, and a second cancel cannot refund again because the guarded update (below) matches no row.

### 5.5 Key transactions

- **Submit (R12–R15, R17):** in one transaction, lock the employee row (`SELECT … FOR UPDATE`) so two submits by the same person cannot both pass the balance check; count working days; check balance and rules; insert the request, its day rows (the unique index rejects overlap with `409`), and the audit, outbox and notification rows.
- **Decide or cancel (R16, R18–R21):** `UPDATE leave_request SET status = …, version = version + 1 WHERE id = :id AND version = :v AND status = :expected`. Zero rows updated → `409 "This request was already decided."` The day rows' `is_active` flag, audit, outbox and notification rows change in the same transaction.
- **Deactivate (R4):** set `is_active = false`, delete sessions, cancel Pending requests (with notification to the manager), all in one transaction.
- **New joiner (R9):** saving an employee with a start date in the current year writes `prorata` entries for Annual and Sick (remaining months, start on day 1–15 counts that month, nearest 0.5), instead of `entitlement` entries.

### 5.6 Scheduled jobs

Run as CLI commands (`python -m app.jobs.<name>`) from scheduled CI workflows using the production `DATABASE_URL`, so no job endpoint is exposed to the internet. All jobs are idempotent. **[Assumption: confirm in the Q5 hello-world that CI scheduling and, for the outbox drain, an in-process background task are acceptable on FastAPI Cloud.]**

| Job | When (company time) | What |
|---|---|---|
| `rollover` | 1 Jan, 00:05 | For each active employee: write the new year's `entitlement` rows (Annual 12, Sick 7) and an Annual `carry_over` of `min(6, unused current-year entitlement)` with `expires_on` = 31 Dec of the new year (R7, Q4; Sick never carries, R8). Idempotency key per employee and year. |
| `expire_carry` | daily, 00:10 | For carried blocks past `expires_on`, write an `expiry` entry for the unused days (R7). |
| `drain_outbox` | in-process, every minute; CI backstop every 15 min | Send due `email_outbox` rows with back-off (R26). |
| `purge` | daily | Delete expired sessions, used or expired tokens, `login_attempt` older than 30 days. |
| `keepalive` | daily | Call `/healthz` so the free-tier project is not paused (§2). |
| `backup` | nightly | `pg_dump` to private storage, 30-day retention (R33). |

## 6. API design

Base path `/api/v1`, JSON only, same origin as the SPA.

### 6.1 Conventions

- **Versioning:** the major version is in the URL path (`/api/v1`). Every route is mounted under a version prefix from one place in the app factory, so a second version can be added as `/api/v2` without moving v1 code. Within a version, changes are additive only (new endpoints, new optional request fields, new response fields); renaming or removing a field, changing a type or status code, or tightening validation needs a new major version. Unknown paths and unsupported versions (e.g. `/api/v9/...`) return `404` in the §6.1 error envelope with code `NOT_FOUND`. When v1 is superseded it stays available for at least one release after `/api/v2` ships and its responses carry `Deprecation: true` and a `Sunset` date header; the SPA is deployed together with the API and calls only the version it was built against. `GET /me` returns `api_version` (`"v1"`) so a stale SPA bundle can detect a mismatch. `/healthz` is unversioned (R33).
- **Auth:** `HttpOnly` session cookie; every non-GET call also sends `X-CSRF-Token` (value from `GET /me`) and must pass the `Origin` check (R29). No session → `401`. The CSRF token is `HMAC-SHA256(session token, "csrf")`, so `GET /me` and the login response can return the same value on every call while only its hash is stored. **[Assumption]** Sign-in throttle: 5 failed attempts per email and 30 failed attempts per IP in a sliding 15 minutes (`LOGIN_IP_LIMIT`); refused attempts are not recorded, so they cannot extend a lock. The client IP is the socket peer, or the right-most entry of `CLIENT_IP_HEADER` when set behind a trusted proxy (A-6). Wrong current passwords on `password/change` count toward the same lockout. **[Assumption]** The common-password check uses a small built-in list, compared lowercase with trailing digits and symbols removed. Invite and reset links are removed from `email_outbox` (body, payload) once the mail is sent or has failed for good; HR cannot retry such a mail and issues a new invite instead (`409`). Sign-in attempts for one email are serialised with a transaction advisory lock, so parallel guesses cannot exceed the 5-failure limit. `GET /me` and the login response send `Cache-Control: no-store`.
- **Dates and times:** `YYYY-MM-DD` for dates, ISO 8601 UTC for timestamps. Half-day values are `full`, `am` or `pm`. Day quantities are numbers in 0.5 steps.
- **Errors:** every error response is JSON with one `error` envelope: `{ "error": { "code": "<MACHINE_CODE>", "message": "<user-facing text>", "details": [ { "field": "<field name>", "issue": "<what is wrong>" } ] } }`. `code` is a stable upper-snake machine code (e.g. `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`); the HTTP status carries the class of error. `message` is the user-facing summary. `details` lists per-field problems and is present for validation failures (`422`, and `400` for unknown fields) and omitted otherwise. `message` and `issue` never contain a stack trace, a note, a rejection reason (except to the employee) or a Sick type. Example (`422`):

  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Request validation failed.",
      "details": [
        { "field": "email", "issue": "Invalid email format." }
      ]
    }
  }
  ```

  **Stack (non-production only):** when `ENVIRONMENT` is not `production` (local, test, staging), an unhandled-error response also carries `error.stack` (string, the formatted traceback) to help debugging. When `ENVIRONMENT=production` the field is never present and the response is the plain envelope; the traceback goes to the server log only. The app defaults to production behaviour when `ENVIRONMENT` is unset or unrecognised. A test must prove `stack` is absent in production for 4xx and 5xx responses.

  Status codes: `400` malformed, `401` no session, `403` not allowed (including an unrelated manager deciding a request, R22), `404` unknown id, `409` conflict (already decided, overlapping leave, stale `version`), `422` rule failed (no working days, balance too low, past date, reason missing), `429` too many sign-in attempts (R2). In production, stack traces are never returned.
- **Validation:** every body is a strict schema; unknown fields are refused (R29).
- **Concurrency:** request objects carry `version`; `approve`, `reject` and `cancel` must send it back. A stale version returns `409`.
- **Creates:** a successful `POST` that creates a resource (requests, employees, teams, holidays, balance entries, HR-entered requests) returns `201 Created` with the new resource in the body and a `Location` header pointing at it, e.g. `Location: /api/v1/requests/{id}`. Actions that change state without creating a resource (approve, reject, cancel, deactivate, login) return `200` with the updated resource, or `204` where there is no body. `POST /auth/reset/request` returns `202`.
- **Lists:** `limit` (default 50, max 200) and an opaque `cursor`; responses are `{ items, next_cursor }`.
- **Redaction by viewer (§8):** the server removes fields the viewer may not see rather than the UI hiding them. `note` is returned only to the owner, the assigned or covering approver while deciding, and HR. The Sick `leave_type` is removed for any viewer outside the §8 "Yes" cells. Calendar entries of masked Sick leave contain only `{ employee, date, slot, label: "Off" }`, with no `leave_type` and no `status` field at all, so Pending and Approved look the same.
- **Roles:** "HR" below means HR admin. "Approver" means an assigned manager, a covering manager, or an HR approver (HR admin or deputy). Role is checked in the service layer on every call (R29).

### 6.2 Endpoints

| # | Method and path | Who | Purpose | R |
|---|---|---|---|---|
| 1 | `POST /auth/login` | Public | Body `{email, password}`. Generic `401` on any failure; `429` after lockout | R1, R2 |
| 2 | `POST /auth/logout` | Any | End the session | R1 |
| 3 | `POST /auth/invite/accept` | Public (token) | `{token, password}`; sets the first password | R3 |
| 4 | `POST /auth/reset/request` | Public | `{email}`; always `202`, same response whether or not the account exists | R3 |
| 5 | `POST /auth/reset/confirm` | Public (token) | `{token, password}`; invalidates all sessions | R3, R2 |
| 6 | `POST /auth/password/change` | Any | `{current_password, new_password}`; invalidates all other sessions | R2 |
| 7 | `GET /me` | Any | Profile, `role`, `is_hr_deputy`, `team`, CSRF token | R1 |
| 8 | `GET /me/balances?year=` | Any | Entitlement, carried (with `expires_on`), used, reserved, available per type | R10 |
| 9 | `POST /requests/preview` | Any | Same body as create; returns `working_days`, per-year split, balance after, `notice_warning`, and rule errors, without saving | R6, R12–R15 |
| 10 | `POST /requests` | Any | Create; returns `201` with `Location`. Body `{leave_type, start_date, start_part, end_date, end_part, note?}`. Returns the request with `status: pending`, routed per R17 | R12–R15, R17 |
| 11 | `GET /me/requests?status=&year=`, `GET /requests/{id}` | Own list; detail for owner, assigned or covering approver, HR | My requests and one request, redacted per §8. HR lists everyone's leave through endpoint 16 | R16 |
| 12 | `POST /requests/{id}/cancel` | Owner (Pending only), HR (Approved or Pending) | Body `{version, reason?}`; `reason` required when HR cancels (R21). Owner on a non-Pending request → `403` | R16, R21 |
| 13 | `GET /approvals?scope=assigned\|cover` | Manager, HR approver | `assigned`: Pending items for me (managers: my reports; HR approvers: the HR queue; deputy: also HR's own requests). `cover`: Pending items of other managers' reports, for the "On behalf of" tab | R17, R20 |
| 14 | `POST /approvals/{id}/approve` | Assigned approver, covering manager, HR approver | Body `{version, on_behalf_of?}`. A cover decision records `decided_on_behalf_of` and emails the direct manager. Own request → `403` | R18, R20, R22, R36 |
| 15 | `POST /approvals/{id}/reject` | Same as 14 | Body `{version, reason}`; `reason` 1–500 non-blank characters | R19, R20 |
| 16 | `GET /hr/leave?status=&from=&to=&employee_id=&team_id=&type=` | HR | All leave, real types | R25 |
| 17 | `POST /hr/requests` | HR | Enter leave for an employee (Sick older than 7 days, R15); body adds `employee_id` and required `entry_reason`; audited; created directly as `pending` for the normal route | R15 |
| 18 | `GET /hr/employees`, `GET /hr/employees/{id}`, `POST /hr/employees`, `PATCH /hr/employees/{id}` | HR | People: name, email, role, team, manager, start date. Create sends the invite and writes pro-rata entries | R1, R3, R9, R23 |
| 19 | `POST /hr/employees/{id}/deactivate` | HR | Deactivate; sessions deleted, Pending cancelled | R4 |
| 20 | `POST /hr/employees/{id}/invite` | HR | Re-send an invite or issue a new link; HR never sees the link | R3 |
| 21 | `GET/POST/PATCH /hr/teams` | HR | Teams | R23 |
| 22 | `GET /hr/deputy`, `PUT /hr/deputy` | HR | Read or assign the one deputy (`{employee_id}` or `null`); audited | R36 |
| 23 | `GET /hr/balances?year=` | HR | Every employee's balances; source of the printable "balances at launch" list | C-9 |
| 24 | `GET /hr/employees/{id}/balances?year=` | HR | One employee's balance and ledger | R24 |
| 25 | `POST /hr/employees/{id}/balance-entries/preview` | HR | Dry run: validates (0–40) and returns the confirmation summary, writes nothing | R24 |
| 26 | `POST /hr/employees/{id}/balance-entries` | HR | Create an opening, carry-over or adjustment entry (`reason` required for adjustment). No update or delete: corrections are new entries | R24 |
| 27 | `GET /holidays?year=` | Any | Holiday list (needed by the request form) | R11 |
| 28 | `POST/PATCH/DELETE /hr/holidays` | HR | Change holidays; response includes `affected_requests` count; audited | R11 |
| 29 | `GET /hr/holidays/impact?date=` | HR | Pending or Approved requests touched by a date, before saving | R11, C-8 |
| 30 | `GET /hr/audit?actor=&action=&target=&from=&to=` | HR | Audit log | R30 |
| 31 | `GET /hr/email-outbox?status=failed` and `POST /hr/email-outbox/{id}/retry` | HR | Failed sends and manual retry | R26 |
| 32 | `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all` | Own only | In-app notifications; another user's id → `403` | R35 |
| 33 | `GET /calendar?month=YYYY-MM&team_id=` **(P2)** | Employee (own team only), manager (own team), HR (any) | Team calendar; masking per 6.1; other team → `403` | R27 |
| 34 | `GET /hr/reports/monthly?month=YYYY-MM&format=xlsx\|csv` **(P2)** | HR | File `leave-report-YYYY-MM.<ext>`, formula-escaped, marked confidential, audited | R28 |
| 35 | `GET /healthz` | Public | Runs `SELECT 1`; returns `{status}` only. Used by monitoring and the keep-alive job | R33 |

The deputy can use endpoints 13–15 and 11 (for requests they decide) and nothing under `/hr/` (R36). Endpoints 2, 6 and 7 are open to every signed-in user.

## 7. Screens

Mobile-first React routes (client-side routing, FastAPI serves `index.html` for unknown non-API paths). Each screen must pass R31.

| Screen | Phase | Contents |
|---|---|---|
| Sign in / Set password / Reset | P1 | Email, password, generic errors |
| Dashboard | P1 | Balances (with carry-over expiry date), upcoming leave, "Request leave" button, pending-approval count for managers |
| New request | P1 | Type, date range, half-day option, live day count and balance-after, notice warnings, note |
| My requests | P1 | List and detail, cancel button on Pending only |
| Approvals | P1 | Items to decide, approve or reject (reason field), "On behalf of" tab for cover |
| HR: All leave | P1 | Filterable list of all leave, cancel Approved (with reason) |
| HR: Employees and teams | P1 | Create, edit, deactivate, assign manager |
| HR: Balances | P1 | Enter opening balances and adjustments, confirmation summary |
| HR: Holidays | P1 | Year list, add, edit, delete, "N requests affected" |
| HR: Audit log | P1 | Searchable log |
| HR: Settings | P1 | Assign the deputy, view and retry failed emails |
| Notification bell | P1 | Unread count, list, mark as read |
| Team calendar | P2 | Month view, team filter (HR), "Off" for Sick |
| HR: Monthly report | P2 | Month picker, preview, export |

## 8. Privacy matrix (who sees which leave type and text)

| Viewer | Own request | Direct report's request | Another manager's report (cover) | Same-team colleague (P2 calendar) | HR |
|---|---|---|---|---|---|
| Leave type | Yes | Yes | Yes (**see C-2**) | Annual/Unpaid: type is shown. Sick: "Off" | Yes |
| Employee's note | Yes | Yes | Yes, only while deciding | No | Yes |
| Rejection reason | Yes | Yes (author) | Yes (author) | No | Yes |
| Balance | Own | No (**Q11**) | No | No | All |

Exports and emails follow the same matrix (R26, R28).

## 9. How each intent constraint is met

| Intent item | Where met |
|---|---|
| Hosting under $5/month | Single FastAPI Cloud service serving API and SPA, managed Postgres, SendGrid (section 2). **Not yet proven: see C-16 and Q5** |
| Low maintenance, one developer | One deployable, no servers to patch, `fastapi deploy` from CI, `/healthz`, outbox with retry, database backups (R26, R33). Rollback is by redeploying the previous tag **[to rehearse on staging]** |
| Go-live 1 Nov, four days, phased | P1/P2 split (section 1). Calendar (R27) and report (R28) deferred. HR "All leave" list (R25) covers HR visibility in P1 |
| ~250 staff, 16 managers, 2 HR (owner and deputy), ~150 requests/month | Single node, indexed queries (R32) |
| New joiners pro-rated | R9 (assumption flagged) |
| Leave types and limits | R5, R7, R8 |
| Full or half days | R12 |
| Notice: 1 day single; 1–2 weeks over a week | R14 (open: Q1, C-3) |
| Direct manager approves; reject needs reason; cover; managers go to HR | R17–R20 |
| Cancellation rules | R16, R21 |
| Working days Mon–Fri excluding Vietnamese public holidays, HR-editable | R6, R11 |
| Calendar rules and sick shown as "Off" | R27, §8 |
| Report content | R28 |
| Login with @asnet.com.vn and password; SSO later | R1–R3, `user_identity` table |
| Email only (Slack/Teams out of scope) | R26 (SendGrid). In-app notifications (R35) are an addition, see C-17 |
| Balances entered by hand at launch | R24 |
| Success: no email requests | R12 plus the emailed links make the tool the only path; the launch note tells staff (see C-1) |
| Success: report under 10 minutes | R28 (P2). Until then HR keeps Excel (intent) |
| Success: no balance corrections | Ledger, derived balances, confirmation step, single day-count function with tests (R6, R10, R24) |
| Out of scope items | Not built. `user_identity` and `leave_type` keep them cheap to add later |

## 10. Test focus (to feed the test matrix)

- Day counting: Fri→Mon = 2, holiday inside range, half days, cross-year split, holiday on a weekend.
- Balance: carried-first consumption, cap of 6, expiry, pro-rata rounding, Pending reservation, refund exactly once.
- Authorization: every endpoint × every role. In particular an unrelated manager approving through the API (R22), and employees reading other teams' calendar.
- Privacy: Sick leave never appears with its type in any email, calendar response or export to non-HR viewers.
- Concurrency: double approve, approve vs cancel at the same time, two simultaneous submits that would overlap or overspend the balance (unique index and employee row lock), a rollover job run twice (idempotency key).
- Data model: `leave_request` checks (half-day shapes, reason required, no self-decision), one-deputy index, append-only `balance_entry` and `audit_log`, anon key reads no table.
- API: strict schemas refuse unknown fields; stale `version` returns 409; redaction removes Sick type and notes server-side for every viewer in §8; deputy gets 403 on every `/hr/` route.

## 11. Open questions carried forward

Answered 2026-10-28 by the product owner, except Q5 (to verify). The last column shows the decision.

| # | Question | Source | Default used in this spec |
|---|---|---|---|
| Q1 | Notice for leave longer than a week: 1 or 2 weeks? Hard block or warning? | Intent | **Decided:** 1 week, warning only (R14) |
| Q2 | Pro-rating: confirm remaining months, rounded to the nearest half day. Is a mid-month start counted? Does it apply to Sick too? | Intent | **Decided:** remaining months; a start on day 1–15 counts that month; Annual and Sick; rounded to nearest 0.5 day (R9) |
| Q3 | Exact date for phase 2 | Intent | **Decided:** Mon 16 Nov 2026 |
| Q4 | Can carried days be carried again, or is the 6-day cap only on the current year's unused days? | Intent | **Decided:** no re-carry; cap applies to current-year unused only (R7) |
| Q5 | Does FastAPI Cloud's plan plus Supabase fit under $5/month? (The Supabase free tier may pause inactive projects and has limited backups; paid tiers cost more than $5.) What are the plan's database, storage, region and rollback options? | New | **Pending:** verify with a hello-world deploy before building (C-16) |
| Q14 | Confirm Twilio SendGrid is the intended email provider; account, plan, sender domain and DNS records ready before 1 Nov? Are in-app notifications wanted at launch? | New | **Decided:** SendGrid email plus in-app notifications at launch (R35) |
| Q13 | Which Supabase plan, region and project owner? Is the free tier acceptable given pausing and backup limits? | New | **Decided:** free tier, Singapore region, developer's personal account for now (transfer to a company account later); keep-alive ping and nightly `pg_dump` mitigate pausing and weak backups |
| Q6 | Which holiday list? | New | **Decided 2026-10-28 (revised):** Vietnamese public holidays incl. compensatory days, not US (R11) |
| Q7 | Half days on the first or last day of a multi-day request? | New | **Decided:** allowed (R12) |
| Q8 | How far back may Sick leave be entered? | New (intent is silent) | **Decided:** employee up to 7 days back; older entries by HR only (R15) |
| Q9 | What does "away" mean for a manager, and who decides? | Intent | **Decided:** any manager can cover, fully audited (R20) |
| Q10 | Retention period for leave records and audit logs | New | **Decided:** 7 years, HR-only access (R34) |
| Q11 | May a manager see the balance of their reports? | New | **Decided:** no; employee and HR only |
| Q12 | Who approves HR's own leave? | New | **Decided:** deputy HR admin role, one named person (R36) |

## 12. Areas of concern

Each item says what conflicts, why it matters, and the recommended decision. **All must be resolved and written back into this spec before the "decide to build" merge.** Status 2026-10-28: all 18 have a written resolution below. C-16 is resolved as a gated check (Q5) that must pass before building.

**C-1. Four days to launch vs "everything is essential" and the success measures.**
The intent gives 4 days from scoping, defers the calendar and report, and keeps HR on Excel for the November month-end. But success is "HR month-end under 10 minutes" and "no balance corrections", and November's month-end falls before or just after phase 2. *Recommendation:* P1 includes the HR "All leave" list (R25), so November's Excel can be fed from it. Set November as "measured, not yet judged". Enter Phase 2 date (Q3) in the launch note. Cut other nice-to-haves before cutting authorization, audit or tests.
**Resolved:** adopt the recommendation. P1 includes R25 so HR can build November's Excel from "All leave". The November month-end is "measured, not yet judged". The launch note states phase 2 ships Mon 16 Nov 2026 (Q3). Authorization, audit and tests are never cut.

**C-2. Sick-leave privacy vs the approval, cover, email and report flows.**
The intent says sick shows as "Off" on the calendar, but the same information flows through other paths: the manager's approval screen, *another* manager covering (R20), email subjects, Pending items on a shared calendar, and balances (a colleague can infer Sick from a team-visible Pending entry). *Recommendation:* the matrix in §8. Emails never name the Sick type (R26). A Sick entry shows as "Off" with the same appearance whether Pending or Approved. Cover managers see type only while deciding. Confirm that direct managers may know the type; this spec assumes yes.
**Resolved:** adopt §8 as written. Direct managers and cover managers see the Sick type only while deciding; emails and in-app notifications never name it; calendar shows "Off" identically for Pending and Approved.

**C-3. Notice rules leave gaps and clash with sick leave.**
"1 day for a single day off" and "1–2 weeks for over a week" leave 2–7 days undefined. "1–2 weeks" is a range, not a rule. "Longer than a week" is calendar days or working days? And a 1-day notice rule makes it impossible to report illness on the day. *Recommendation:* Sick is exempt (R15). Define "longer than a week" as more than 5 working days. Treat 2–7 days as no notice (R14) unless HR says otherwise. This needs HR's answer (Q1).
**Resolved:** Sick is exempt (R15). "Longer than a week" means more than 5 working days. Per Q1 the notice is 1 week and warning only. Requests of 2–5 working days have no notice rule. Single-day Annual/Unpaid keeps the 1-day hard block.

**C-4. Backdating is not in the intent, but sick leave needs it.**
Without a rule, staff who fall ill cannot record the absence, and HR will fix it by hand, which is the correction work the project is meant to remove. *Recommendation:* allow Sick up to 7 days back (Q8). Annual and Unpaid stay in the future (R13).
**Resolved:** Q8 applies: employee up to 7 days back for Sick; older entries by HR only, with a reason, audited (R15).

**C-5. "Any other manager can approve if the direct manager is away" is an unverifiable, broad permission.**
The system cannot know that someone is away. Any of 15 managers can approve any request, which weakens separation of duties, widens who sees personal data, and makes "approved by the wrong person" disputes possible. *Recommendation:* ship as the intent says, with an on-behalf-of screen (not the default list), a full audit entry, and an email to the direct manager (R20). A later hardening option is for the direct manager (or HR) to mark themselves "away" with dates. Needs sign-off from HR (Q9).
**Resolved:** Q9 applies: any manager can cover, via the "On behalf of" tab only, with a full audit entry and an email to the direct manager (R20). An "away" flag with dates is the first hardening option after launch.

**C-6. HR is a single person with every power and no approver of their own.**
HR manages employees, edits balances, cancels approved leave, approves managers' requests and sees all data. There is no one to approve HR's leave, nobody to cover HR's absence (managers' requests then stall), and no second pair of eyes on balance edits. *Recommendation:* the audit log (R30) is mandatory. Add a deputy HR admin role, assigned to one named person, to approve HR's own leave and cover absence. This conflicts with the intent's "HR (1 person)" count and needs a decision (Q12).
**Resolved:** Q12 applies: one named deputy HR admin, approval and cover only (R36). Audit log is mandatory (R30). The intent now says 2 HR people (owner and deputy).

**C-7. Carry-over wording is ambiguous.**
"Expire 31 Dec of the following year" (intent) reads as: days carried into 2027 expire 31 Dec 2027. It also means a day unused in 2026 can live until the end of 2027, so the effective "use it or lose it" period is two years. Together with the open Q4, it is unclear whether the 6-day cap measures the old carried days or only the current year's. *Recommendation:* the ledger model (R7) handles either reading. Adopt: cap applies to current-year unused only; carried days expire, never re-carry.
**Resolved:** Q4 applies exactly as recommended (R7). Carry-over entries show their expiry date on the Dashboard (R10).

**C-8. Editing public holidays after leave is booked.**
HR can edit holidays (intent). Adding a holiday inside an Approved range changes its day count and the balance, retroactively, and may also break "no balance corrections". *Recommendation:* `working_days` is a snapshot. HR sees the list of affected requests (R11) and applies an explicit audited adjustment where needed, never silent recalculation.
**Resolved:** adopt as written (R11, R24). `working_days` stays a snapshot; HR adjusts through ledger entries.

**C-9. Manual entry of ~250 starting balances in a few days is the biggest accuracy risk.**
CSV import is explicitly deferred, history is not imported, and the success measure is "no balance corrections". A typing error is a balance correction. *Recommendation:* confirmation summary and range limits (R24), a printable "balances at launch" list for staff to check and report mistakes in week 1, and an append-only ledger so corrections are traceable. Consider asking for CSV import to be reconsidered, as it removes most of the risk.
**Resolved:** keep manual entry; CSV import stays out of scope. Safeguards are mandatory in P1: confirmation summary and 0–40 range (R24), a printable "balances at launch" list that staff check in week 1, and the append-only ledger.

**C-10. Pending requests: reserve days or not?**
The intent says days are "refunded" when HR cancels Approved leave, which implies deduction on approval. But if Pending requests do not reserve days, an employee can submit five requests that together exceed their balance. *Recommendation:* reserve on submit, release on reject or cancel (R10).
**Resolved:** confirmed. Pending requests reserve days; Available = entitlement + carried − used − reserved (R10).

**C-11. Password login for a system holding HR data, with SSO planned later.** Controls are R2, R3 and R29. Because auth is built in-house, see C-18.
Password login adds attack surface (credential stuffing, reset abuse), and a budget host with no WAF increases it. *Recommendation:* R2/R3/R29 controls, no HR-set passwords, and the identity table for SSO. Consider making Google SSO the first post-launch item rather than a vague "later".
**Resolved:** R2, R3, R29 controls apply; Google SSO is the first post-launch item.

**C-12. Company location and time zone are unclear.**
The login domain is `@asnet.com.vn`, but the intent originally specified *US* public holidays (now revised to Vietnamese, see Q6) (the interview notes mention an Austin, Texas company). "1 day's notice", "today", the leave-year boundary and holiday dates all depend on a time zone. If staff are in more than one country, US holidays may be wrong for many people. Non-US calendars are out of scope. *Recommendation:* one configurable company time zone. Confirm that all staff work to the US calendar (Q6).
**Resolved:** company time zone is `Asia/Ho_Chi_Minh`, set by one configuration value (`COMPANY_TZ`). It governs "today", the 1-day notice, the leave-year boundary and holiday dates. All staff follow the Vietnamese public holiday calendar (Q6, revised: the intent said US).

**C-13. Reports and exports are the highest-risk data release.**
The report lists who was off and when, by type, for all staff, in a file that leaves the system. The privacy rule in the intent covers only the calendar. *Recommendation:* HR-only, audited, formula-escaped (R28), and the file is marked as confidential. State this in the HR guide.
**Resolved:** adopt as written (R28): HR-only, audited, formula-escaped, marked confidential.

**C-14. Retention and removal of personal data is not defined.**
No retention rule exists, and staff leaving still have sick-leave history. *Recommendation:* R34 default, and Q10 to be decided by HR/legal.
**Resolved:** Q10 applies: 7 years, HR-only access (R34).

**C-15. Interview notes and intent disagree on some facts.**
`ref/claude-qna.md` says 5 sick days and about 26 requests a month, while the intent says 7 sick days and about 150 requests a month. The intent is the source of truth, and this spec uses 7 and 150. The old numbers should be corrected or removed to avoid someone building from them.
**Resolved:** the intent wins (7 sick days, ~150 requests/month). Action: correct the two figures in `ref/claude-qna.md` before the build merge.

**C-16. FastAPI Cloud and a React SPA may break the "under $5/month" constraint and the "SQLite, no database server" design.**
The earlier stack avoided a database server and a build step to stay cheap and low-maintenance. FastAPI Cloud is a good fit for the Python code and for serving a built SPA from the same domain, but a web search found no public pricing and no confirmed managed database or persistent disk. So three assumptions are unverified: the app plan fits the budget, the app filesystem is ephemeral (so SQLite is unsafe), and a managed Postgres is available at a price that keeps the total under $5. A Node build step in CI is also new maintenance work for a one-developer team. *Recommendation:* before building, check pricing and database options on the FastAPI Cloud documentation and deploy a hello-world service with the database connected. If the total exceeds $5/month, either get an explicit budget exception or fall back to the earlier single-VPS design. Do this first, because the whole stack depends on it. Needs a decision from the product owner (Q5, Q13).
**Resolved:** build is gated on a hello-world deploy with the database connected (Q5, Q13). Pass: total ≤ $5/month. Fail: request a budget exception from the product owner first (decided 2026-10-28); the single-VPS design is the fallback only if it is refused. The developer runs the check on 29 Oct 2026. Do this first, before any feature work.

**C-17. Email depends on an external account and DNS being ready within four days; in-app notifications go beyond the intent.**
Invite and reset links (R3) and approval alerts only work if SendGrid is set up and the sender domain is authenticated (SPF, DKIM, DMARC). Until then new users cannot set a password and managers are not alerted, which risks staff falling back to email and failing the first success measure. "Twilio" also sells SMS and voice, so this spec assumes SendGrid. In-app notifications (R35) are added as a safety net, but the intent says email only, so this is scope the product owner has to accept. *Recommendation:* start the SendGrid account and domain verification now, send a test invite to a real mailbox in staging, and keep the in-app bell as the fallback. Needs confirmation (Q14).
**Resolved:** Q14 applies: SendGrid plus in-app notifications at launch (R35). Start SendGrid account and SPF/DKIM/DMARC verification now; a test invite to a real mailbox on staging is a go-live gate.

**C-18. Building auth ourselves raises the security burden on a one-developer, four-day project.**
Password storage, lockout, reset flows, session handling and CSRF are common sources of serious flaws, and nothing here is provided by a vendor. Supabase is used as a database only, so its Auth and its public REST API must be unused: RLS-on-everything with no policies (section 2) is mandatory, and a test must confirm the anon key can read no table. Specific risks: account enumeration through error text or timing (R1, R3), weak reset tokens, session fixation, missing rate limits, and password reset email (SendGrid) failing, which blocks every new user. *Recommendation:* use well-tested libraries (Argon2id via `argon2-cffi`, `secrets` for tokens, no custom crypto), write the authorization and auth tests first, run the `security-review` skill on the auth module before launch, and treat Google SSO as the first post-launch item to remove password handling.
**Resolved:** adopt as written. Go-live gates: auth and authorization tests written first, a test proving the Supabase anon key reads no table, and `security-review` run on the auth module.

## 13. Decisions log

Decided on 2026-10-28 (product owner). Concerns still need a written decision unless noted.

| Item | Decision | By | Date |
|---|---|---|---|
| Q1 | 1 week notice for leave over a week; warning only, never a hard block | Product owner | 2026-10-28 |
| Q2 | Pro-rate by remaining months (start day 1–15 counts that month), Annual and Sick, nearest 0.5 day | Product owner | 2026-10-28 |
| Q3 | Phase 2 (calendar and report) ships Mon 16 Nov 2026 | Product owner | 2026-10-28 |
| Q4 | Carried days are not carried again; cap applies to current-year unused days | Product owner | 2026-10-28 |
| Q5 | Verify FastAPI Cloud + Supabase pricing and limits with a hello-world deploy before building. Supabase: free tier, Singapore | Product owner | 2026-10-28 |
| Q14b | SendGrid account owned by the product owner, who also sets up SPF/DKIM/DMARC for the sender domain before 1 Nov | Product owner | 2026-10-28 |
| Holidays | Seed list drafted in Appendix A (unverified); the developer verifies it against the government decree by 30 Oct 2026 | Product owner | 2026-10-28 |
| Q5 owner | Developer runs the hello-world deploy and cost check on 29 Oct 2026. If the total exceeds $5/month, request a budget exception from the product owner before choosing another design | Product owner | 2026-10-28 |
| Q13 ownership | Supabase stays on the developer's personal account with no transfer date; accepted as a known risk (company HR data on a personal account) | Product owner | 2026-10-28 |
| Training refs | `ref/leavedesk-2-solutions.md` R6-AC3 (recalculate on holiday change) left as the exercise's reference answer; the real spec (C-8) does not recalculate | Product owner | 2026-10-28 |
| Policy | Keep 7 paid sick days, 7-day sick backdating, Jan–Dec leave year in `Asia/Ho_Chi_Minh` | Product owner | 2026-10-28 |
| Q6 | Vietnamese public holidays (incl. compensatory days) preloaded; replaces the intent's US calendar | Product owner | 2026-10-28 |
| Q7 | Half days allowed on first and last day of multi-day requests | Product owner | 2026-10-28 |
| Q8 | Sick leave: employee up to 7 days back; older dates entered by HR only | Product owner | 2026-10-28 |
| Q9 | Any manager may cover an absent manager; audited, direct manager notified | Product owner | 2026-10-28 |
| Q10 | Retain records 7 years, HR-only access | Product owner | 2026-10-28 |
| Q11 | Managers do not see their reports' balances | Product owner | 2026-10-28 |
| Q12 | One named deputy HR admin approves HR's leave and covers HR (R36) | Product owner | 2026-10-28 |
| Q13 | Supabase project on the developer's personal account for now | Product owner | 2026-10-28 |
| Q14 | SendGrid email and in-app notifications at launch | Product owner | 2026-10-28 |
| C-3 | "Longer than a week" = more than 5 working days; 2–5 working days have no notice rule | Product owner | 2026-10-28 |
| C-9 | Keep manual balance entry (no CSV import) with confirmation, range limits and a launch balance list | Product owner | 2026-10-28 |
| C-10 | Pending requests reserve days on submit; released on reject or cancel | Product owner | 2026-10-28 |
| C-12 | Company time zone `Asia/Ho_Chi_Minh` (configurable); Vietnamese public holiday calendar for all staff | Product owner | 2026-10-28 |
| C-1, 4–8, 13–15, 17 | Recommendations adopted as written in section 12 | Product owner | 2026-10-28 |
| C-2 | Direct and cover managers may see the Sick type while deciding | Product owner | 2026-10-28 |
| C-11, C-18 | In-house auth, Google SSO first after launch, security-review gate before go-live | Product owner | 2026-10-28 |
| HR count | HR is 2 people (owner and deputy); intent updated | Product owner | 2026-10-28 |
| C-16 | Gated on the Q5 hello-world deploy and cost check before building | Product owner | 2026-10-28 |

## Appendix A. Vietnamese public holiday seed (press-reported, decree text not yet checked)

Seeded by migration `0005` exactly as listed, one row per weekday. Compiled on 30 Oct 2026 from press reports of the Ministry of Home Affairs notices (including notice 11483/TB-BNV of 9 Oct 2026 for Tet and National Day 2027) and the National Assembly resolution making 24 Nov Vietnam Culture Day a paid holiday. The decree and notice texts themselves could not be opened from the build environment, so the developer still confirms each date against them (A-19, go-live gate) and corrects it in the Holidays screen. The public-sector days (2 Jan 2026, 31 Aug 2026, 3 Sep 2027, the Tet block) are included on the Q6 assumption that the company follows the government schedule; Q6 should confirm that for private-sector employers.

| Date | Holiday | Status |
|---|---|---|
| 2026-01-01, 2026-01-02 | New Year's Day and the extra day | Press-reported (make-up Sat 10 Jan 2026 is not modelled: Saturday shifts are out of scope) |
| 2026-02-16 to 2026-02-20 | Tet (17 Feb 2026); holiday 14 to 22 Feb, weekdays only | Press-reported |
| 2026-04-27 | Hung Kings' Commemoration (lunar 10/3 is Sun 26 Apr), compensatory Monday | Verify |
| 2026-04-30, 2026-05-01 | Reunification Day, International Labour Day | Fixed |
| 2026-08-31, 2026-09-01, 2026-09-02 | National Day block (29 Aug to 2 Sep; make-up Sat 22 Aug not modelled) | Press-reported |
| 2026-11-24 | Vietnam Culture Day | Press-reported (sources disagree on whether the day was shifted to Mon 23 Nov; none confirmed) |
| 2027-01-01 | New Year's Day | Fixed |
| 2027-02-04, 2027-02-05, 2027-02-08 to 2027-02-10 | Tet (6 Feb 2027); public-sector holiday Thu 4 to Wed 10 Feb | Press-reported |
| 2027-04-16 | Hung Kings' Commemoration | Verify |
| 2027-04-30 | Reunification Day | Fixed |
| 2027-05-03 | Labour Day compensatory Monday (1 May is a Saturday) | Verify |
| 2027-09-02, 2027-09-03 | National Day and the extra day | Press-reported (private employers may grant 1 Sep or 3 Sep) |
| 2027-11-24 | Vietnam Culture Day | Press-reported |
