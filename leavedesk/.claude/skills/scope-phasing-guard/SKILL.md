---
name: scope-phasing-guard
description: Guards LeaveDesk scope, phasing, cost/maintenance constraints, open questions and traceability to the intent. Use at the start and end of every spec section, when adding a requirement, or when making a technology or hosting choice.
---

Source of truth: `intent/leave-management-tool.md`.

## Rules
1. Tag every requirement Phase 1, Phase 2, or Out of scope.
   - Phase 2 (about two weeks after the 1 Nov 2026 go-live): team calendar and monthly report.
   - Out of scope: Google SSO at launch, Slack/Teams, Excel history import, CSV balance import, extra leave types, non-US holidays, Saturday/shift patterns.
2. Every requirement cites its intent line. Anything uncitable is labelled `ASSUMPTION` and listed for the user to approve. Never invent business decisions.
3. Constraints to check every design choice against: hosting/running cost under $5/month; low maintenance; modest load (~250 staff, ~150 requests/month); very tight deadline.
4. Keep open questions visible as open: notice period and block vs warning; pro-rating; Phase 2 date; re-carry of carried days. Do not silently settle them in the spec.
5. Success measures: no leave requests by email after launch; month-end report under 10 minutes (reachable only after Phase 2); no balance corrections needed. Note dependencies on phasing.

## Trigger
Starting or finishing a spec section; adding any requirement; choosing hosting, email provider, database or framework.

## Consistency checks
- A traceability table maps intent line -> requirement -> success measure.
- No Phase 1 requirement depends on a Phase 2 feature.
- Nothing from the Out of scope list has crept in.
- Every `ASSUMPTION` and open question is listed in one place.
- Cost and maintenance impact is stated for each infrastructure choice.
