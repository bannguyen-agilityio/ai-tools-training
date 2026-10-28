---
name: access-privacy-audit
description: Keeps LeaveDesk authentication, role permissions, data visibility, sick-leave masking and audit trail consistent. Use when writing or reviewing anything about login, roles, who can see leave, reports/exports, emails showing leave, or HR-editable data.
---

Source of truth: `intent/leave-management-tool.md`.

## Rules
1. Roles are exactly Employee, Manager (16), HR (1). Add no others.
2. Maintain ONE role x data x action matrix. Deny by default; enforce on the server, not only in the UI.
3. Login: @asnet.com.vn email and password at launch; Google SSO later (out of scope for launch). Passwords stored hashed; sessions secured.
4. Visibility the intent defines:
   - Employees see their own balance and their team's calendar (Phase 2).
   - Team members see their team's approved AND pending leave.
   - HR sees all teams and all approved leave.
   - Managers act on requests of their reports.
   - Sick leave shows as "Off" on the calendar.
5. Apply the "Off" masking wherever other people's leave appears: calendar, emails, any list. HR's report lists leave by type per the intent.
6. HR-only actions: manage employees, teams, managers, holidays, starting balances; cancel Approved leave; approve managers' requests.
7. Audit: log every HR change and every balance-affecting event with who, when, old value, new value.
8. Open items: whether managers see leave type beyond approval; password reset/policy; SSO account linking; whether HR may adjust balances after launch.

## Trigger
Any spec section on login, roles, screens/endpoints/exports showing leave, email content, or HR-editable data.

## Consistency checks
- Every screen, endpoint and export appears in the matrix.
- Masking is identical in calendar, report views and emails.
- Every HR-editable item has an audit entry.
- Phase 2 views are covered by the same matrix.
- Actors match `leave-request-workflow` transitions.
