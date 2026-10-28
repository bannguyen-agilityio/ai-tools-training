# Intent: LeaveDesk, internal leave management tool

## Problem
HR tracks leave in Excel files. Checking and updating records and preparing the monthly report takes about 2 days a month for roughly 150 requests a month across ~250 staff. Requests arrive by email, and balances are error-prone and need corrections.

## Proposed outcome
A simple web tool where staff request leave, managers approve or reject it, and balances (with carry-over and public holidays excluded) are calculated automatically. HR can see all approved leave and export a monthly report.

- **Leave types:** annual (12 days/yr, up to 6 unused days carry over, carried days expire 31 Dec of the following year), sick (7 paid days/yr, no carry-over), unpaid (unlimited). Leave year is Jan–Dec.
- **Requests:** full or half days (morning/afternoon). Notice: 1 day for a single day off; 1–2 weeks for leave longer than a week.
- **Approval:** direct manager approves or rejects (rejection needs a reason). Any other manager can approve if the direct manager is away. Managers' own requests go to HR.
- **Cancellation:** employee while Pending; only HR once Approved (days refunded).
- **Working days:** Mon–Fri excluding Vietnamese public holidays (preloaded, HR-editable).
- **Calendar (phase 2):** team members see their team's approved and pending leave; HR sees all teams; sick leave shows as "Off".
- **Report (phase 2):** monthly Excel/CSV with leave taken per employee by type, remaining balances, and who was off and when.

## Affected users and systems
- **Employees (~250 staff in total):** request leave, view balance and team calendar.
- **Managers (16):** approve or reject requests for their reports.
- **HR (2 people: HR owner and a deputy):** manages employees, teams, managers, holidays and starting balances; sees all leave; cancels approved leave; approves managers' requests.
- **Systems:** email (notifications). Login with @asnet.com.vn email and password, with Google SSO later. The Excel files are replaced; balances are entered by hand once at launch.

## Constraints
- Hosting and running cost under $5/month.
- A developer is available for support; the tool should be low-maintenance.
- Go-live 1 November 2026, with only four days left when scoped, so release is phased.
- Modest load: ~250 staff (16 managers, 1 HR), about 150 requests a month.
- New joiners get pro-rated leave (assumed by remaining months, rounded to the nearest half day).

## Success measures
- No leave requests arrive by email after launch.
- HR month-end reporting takes under 10 minutes (down from about 2 days).
- No balance corrections are needed.

## Out of scope
- Google SSO at launch (added later).
- Slack/Teams notifications (email only).
- Importing Excel history or past leave records.
- CSV import of balances: deferred to a later phase. At launch HR enters balances by hand.
- Leave types beyond annual, sick and unpaid; non-Vietnamese holiday calendars; Saturday/shift work patterns.
- **Release phasing:** team calendar and monthly report are deferred to about two weeks after 1 Nov. HR keeps using Excel for the month-end report until then.

## Decisions (2026-10-28)
- Leave longer than a week (more than 5 working days): 1 week notice, warning only, never a hard block.
- New-joiner pro-rating: remaining months (start on day 1-15 counts that month), annual and sick, rounded to the nearest half day.
- Phase 2 (calendar and report) ships Mon 16 Nov 2026.
- Carried-over days are not carried again; the 6-day cap applies to the current year's unused days only.
- Holidays: Vietnamese public holidays (replaces the earlier US calendar).
- HR is 2 people: the HR owner and one deputy.

See `leave-management-tool/spec.md` for the full decisions log.
