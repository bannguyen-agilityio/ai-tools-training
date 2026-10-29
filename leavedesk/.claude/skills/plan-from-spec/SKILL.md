---
name: plan-from-spec
description: Writes or updates implementation plans from a spec's intent and requirements, for new requirements or changes to existing ones. Use when the user asks to plan, break down, or re-plan R-numbers, a spec change, or a new feature in specs/<NNN>-*/.
---

Plans describe future PRs. Writing a plan never writes application code.

## 1. Find the sources

1. Locate the spec folder `specs/<NNN>-<name>/` (the one the user names; if only one exists, use it). Read `intent.md` in full, then `spec.md` sections relevant to the request: requirements (§4), data model (§5), API (§6), screens (§7), privacy (§8), concerns (§12), decisions (§13). Read `plans/README.md` and any existing plan that touches the same requirements.
2. Read `CLAUDE.md` rules (stack, architecture, privacy, conventions); plans must obey them.

## 2. Classify the request

- **New**: requirement(s) with no plan yet (not in the README table).
- **Change**: a requirement, decision or concern that was edited, or a plan that is now stale. Diff against the existing plan (and `git log -p` on the spec if needed) and edit that plan in place; do not create a duplicate.
- If the request is not covered by the intent or spec, stop and tell the user. Propose a spec change (marked **[Assumption]**) first; do not plan from guesses.
- Group requirements into one plan only when they share files, tables or a PR-sized vertical slice (as in `R-005-R-007-R-008.md`).

## 3. Write the plan

Save as `specs/<NNN>-<name>/plans/R-<id>[-R-<id>...].md` (zero-padded, ascending, e.g. `R-012-R-013-R-017.md`). Use exactly this structure, matching the existing plans:

```
# Plan <NN>: <R-ids> <short title>

Phase P1|P2. Depends on: <plan numbers and why>. Blocks: <plans or none>.

## Requirements and acceptance criteria
- **R#**: the requirement in one line, quoting the spec's wording; add C-#/§ refs and API endpoint numbers.

## Files
Create: ... Modify: ... Delete: ...   (paths follow the vertical module layout: router, service, repository, models, schemas, dependencies; tests; migrations; frontend slice)

## Steps
Numbered, ordered. Tests first for auth, authorization and balance. Include the UI slice, audit rows, notification events and migration.

## Risks and dependencies
Edge cases, concurrency, privacy exposure, shared files. Cite ambiguity IDs (A-#) or spec concerns (C-#).

## Tests proving each criterion
Table: Criterion | Test.

## Definition of done
Baseline DoD (from plans/README.md) plus extras only.
```

Rules:
- Every acceptance criterion maps to a test row. Every endpoint lists 401 and per-role 403 tests.
- Apply CLAUDE.md invariants: derived balances via `compute_balance`, append-only ledger/audit, server-side redaction of Sick type, notes and rejection reasons, strict schemas, `problem+json`, optimistic locking with `version`, `COMPANY_TZ`.
- Use `add-endpoint` for new endpoints in Steps; `security-review` for auth work.
- Respect phase limits: P1 go-live 1 Nov 2026, P2 16 Nov 2026. Never plan to cut authorization, audit or tests.
- Where the spec is ambiguous, do not decide. Add or reuse an A-# entry, state which behaviour is implemented only if the spec is explicit, and otherwise mark the step blocked.
- Do not invent facts, figures or R-numbers. Out-of-scope items stay out.
- Match the existing plans' density: terse bullets, no prose padding.

## 4. Keep the index in sync

Update `plans/README.md` in the same change:
- Add or edit the plan's row in the dependency table (number, file, R-numbers, phase, depends on).
- Update the wave table, dependency chains, parallel summary and shared-file notes if ordering changed.
- Add new ambiguities to the register with the next A-# id.
- Check every R# is still covered exactly once.

If the plan reveals the spec is wrong or incomplete, fix `spec.md` in the same change (per CLAUDE.md) and log it in §13.

## 5. Finish

- Commit with a conventional message, e.g. `docs: add plan for R-0xx`, citing R#/C-#. Do not commit unless the user asked.
- Report to the user: files created or changed, new ambiguities (A-#), and any spec edits needed.
