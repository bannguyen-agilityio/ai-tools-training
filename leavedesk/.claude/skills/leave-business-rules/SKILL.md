---
name: leave-business-rules
description: Keeps LeaveDesk balance and day-count rules consistent between requirements and spec. Use when writing or reviewing anything about leave types, balances, carry-over, working days, half days, public holidays, notice periods, pro-rating, or report numbers.
---

Source of truth: `intent/leave-management-tool.md`.

## Rules
1. Keep all business rules in ONE rules table with stable IDs (`BR-01`, `BR-02`, ...). Other sections cite the ID and never restate the rule.
2. Rules the intent defines:
   - Annual: 12 days/yr; up to 6 unused days carry over; carried days expire 31 Dec of the following year.
   - Sick: 7 paid days/yr; no carry-over.
   - Unpaid: unlimited.
   - Leave year: Jan-Dec.
   - Full or half days (morning/afternoon).
   - Working days: Mon-Fri excluding US public holidays (preloaded, HR-editable).
   - Notice: 1 day for a single day off; 1-2 weeks for leave longer than a week.
   - New joiners: pro-rated by remaining months, rounded to nearest half day (assumption, unconfirmed).
3. Day counts and balances are always derived from working days and recorded transactions. Never accept a typed-in day count.
4. Half day = 0.5. Never invent numbers, thresholds or behaviours the intent does not state. Write `TBD (OQ-n)` and link the open question.
5. Every rule gets a worked example, including edge cases: spanning a holiday, a weekend, a year boundary, and a half day.
6. Known open items, which must stay marked open until the user answers: notice 1 vs 2 weeks and hard block vs warning; pro-rating method; re-carry of carried days; behaviour when a request exceeds the balance; whether Pending days reserve balance; use order of carried vs current days; effect of editing a holiday on existing leave.

## Trigger
Any spec section touching balances, day counts, leave types, notice, holidays, carry-over, pro-rating, or numbers in the report.

## Consistency checks
- Every calculation in the spec, UI text and report cites a `BR-` ID.
- Every `BR-` rule has a worked example.
- No rule appears twice with different wording.
- Each open question is flagged on the rule it affects.
- Sick leave never carries over; unpaid never has a limit; no figure differs from the intent.
