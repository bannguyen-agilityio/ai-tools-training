---
name: leave-request-workflow
description: Keeps LeaveDesk request lifecycle, approval routing, cancellation, notifications and UX/accessibility baseline consistent. Use when writing or reviewing anything about requesting, approving, rejecting, cancelling, delegation, emails, or screens/forms.
---

Source of truth: `intent/leave-management-tool.md`.

## Rules
1. Define the lifecycle as ONE state-transition table: from state, to state, actor, precondition, balance effect, notification. States: Pending, Approved, Rejected, Cancelled.
2. Transitions the intent allows (add no others):
   - Employee submits -> Pending.
   - Direct manager approves or rejects. Rejection requires a reason.
   - Any other manager may approve if the direct manager is away.
   - A manager's own request goes to HR for approval.
   - Employee cancels while Pending.
   - Only HR cancels once Approved, and the days are refunded.
3. Everything not listed is denied. For example, an employee cannot cancel an Approved request. Editing a Pending request is not in the intent: flag it as a question, do not specify it.
4. Each balance-affecting transition cites the `BR-` rule from `leave-business-rules`.
5. Email is the only notification channel (no Slack/Teams). Each notification maps to exactly one transition.
6. Open items to keep visible: how "away" is determined; who approves HR's own leave; escalation of stale Pending requests; email failure handling.

## UX and accessibility baseline (lightweight, state only what is needed)
- The tool is "simple": few screens, one primary action each (request, approve/reject, cancel).
- Half-day choice (morning/afternoon) is explicit. Show the computed working days and the resulting balance before submitting.
- Show state with text, not colour alone. Keep keyboard-operable forms with labelled inputs and error messages that say what to fix.
- Calendar (Phase 2): sick leave displays as "Off" as a text label.
- Do not add UX requirements beyond this without asking.

## Trigger
Any spec section on requesting, approving, rejecting, cancelling, delegation, notifications, or screen/form behaviour.

## Consistency checks
- Each user story maps to a transition, and each transition maps to a story.
- Every state is reachable and is terminal or has an exit.
- Every actor in a transition exists in `access-privacy-audit`'s role matrix.
- Every notification maps to a transition; every refund matches `BR-` rules.
