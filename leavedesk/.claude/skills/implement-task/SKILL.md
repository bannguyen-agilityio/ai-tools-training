---
name: implement-task
description: Implements a LeaveDesk GitHub Project task end to end: finds the issue, moves it on the board, builds it on a branch, tests, opens a PR, and updates the board. Use when the user gives a GitHub issue number or title and asks to implement, build, work on, or ship it.
---

Runs the full task workflow from board to pull request. Input: an issue number or title (`$ARGUMENTS`). Use `gh` for everything. Run from the repo root. Never read `ref/`.

## 0. Preflight

1. `gh auth status`. Board commands need `project` and `read:project` scopes. If missing, stop and ask the user to run `! gh auth refresh -s project,read:project`.
2. `gh repo view --json nameWithOwner,owner`. `git status`: note any uncommitted changes. Preserve them; never stash, reset or commit unrelated files.
3. Board: `gh project list --owner <owner> --format json`, use "LeaveDesk" unless the user names another. Get field ids and the Status option ids with `gh project field-list <n> --owner <owner> --format json`.

## 1. Find the task

1. Number: `gh issue view <n> --json number,title,body,state,assignees,labels,url`. Title: `gh issue list --state all --search "<title> in:title" --json number,title,state`.
2. Zero or several plausible matches: ask the user which one. Closed issue: confirm before continuing.
3. Read the body for requirements and acceptance criteria. Read the plan file it came from in `specs/<NNN>-*/plans/` and the R#/C-# sections it cites in `spec.md`. If the plan and spec disagree, the spec wins; fix the spec in the same change (CLAUDE.md).
4. Check dependencies: "blocked by" or "depends on" references, and sub-issues (`gh api repos/<repo>/issues/<n>/sub_issues`). If a dependency is open and the work cannot proceed without it, stop and report. Ask only when the task is ambiguous or a critical decision is the user's.

## 2. Move to In Progress

1. Find the item id: `gh project item-list <n> --owner <owner> --format json --limit 200`, match by issue number.
2. If the issue is not on the board, add it: `gh project item-add`.
3. `gh project item-edit --id <item> --project-id <proj> --field-id <status> --single-select-option-id <In Progress>`.
4. Assignees: if none, assign the current user (`gh issue edit <n> --add-assignee @me`). Never remove existing assignees.
5. Re-read the item and confirm Status is `In Progress`.

## 3. Implement

1. Read `CLAUDE.md` rules that apply (stack, privacy, architecture, conventions) and inspect the surrounding code before writing.
2. Branch off up-to-date `main`: `git switch -c <type>/<n>-<short-slug>` (`feat/`, `fix/`, `docs/`, `refactor/`).
3. For new endpoints use the `add-endpoint` skill.
4. Order per CLAUDE.md: auth, authorization and balance tests first. Never cut authorization, audit or tests. Respect the privacy rules (server-side redaction, no Sick type or notes in emails, logs or exports).
5. Stay within the task's scope. Mark anything not in the intent as **[Assumption]** in the spec.

## 4. Test and verify

Run what is relevant to the change, and report real output:

- Backend: `pytest` (targeted, then full), `ruff check`, `ruff format --check`, `mypy`.
- Frontend: `vitest run`, `eslint`, `tsc --noEmit`.
- Fix failures that your change caused and rerun. If something cannot run (missing tooling, no DB, no network) or fails for an unrelated reason, say so; never claim a pass you did not see. Check each acceptance criterion and record how it was verified.

## 5. Code review and security review

Review before committing, on the working-tree diff (`git diff` plus new files).

1. **Code review:** run the `review-checklist` skill (correctness, tests, readability, security basics, scope), then `code-review` at `medium` effort. Do not use `max` or `ultra` unless the user asks.
2. **Security review:** always run the `security-review` skill, for every task (CLAUDE.md Conventions). All three skills (`review-checklist`, `code-review`, `security-review`) must have run before step 6 creates the PR. Pay particular attention when the change touches auth or sessions, authorization checks, CSRF or Origin handling, request schemas, SQL or migrations, RLS, email or notification content, audit or logging, exports or reports, or privacy redaction (Sick type, notes, rejection reasons). If a skill cannot run, say so in the PR instead of skipping it silently.
3. Fix every confirmed correctness, security or privacy finding, then rerun step 4 on the affected checks. Do not fix style nits outside this task's scope; list them instead.
4. Skip nothing silently. Record each finding with its outcome (fixed, not fixed with reason, or false positive) for the PR body and the report. If a finding is serious and cannot be fixed in scope, stop before pushing and ask the user.

## 5b. Record open items in the plan

Before committing, append every concern that stays open to the task's plan file in `specs/<NNN>-*/plans/`, under a `## Open items (after PR #<n>)` heading (create it; update it if it exists). Include: unfixed review findings, checks not run (e2e, full pytest, pyright, staging), deviations from the plan, **[Assumption]** items, and decisions deferred to a later slice (name the slice). One bullet each, with what is wrong and where it should be fixed. Remove items you fixed. Commit the plan change with the code, and link the section from the PR body. If nothing is open, write "None" rather than skipping it.

## 6. Commit, push, PR

1. `git status` / `git diff`: stage only files for this task by name.
2. Conventional commit citing R#/C-# and the issue (`feat: ... (R12, #<n>)`). End with the attribution line given in the session reminder.
3. `git push -u origin <branch>`. Never force-push. If the pre-push hook fails, fix and retry; do not bypass it.
4. Use the `pr-description` skill for the body. Include `Closes #<n>`, a summary, the acceptance-criteria checklist, and the test results exactly as observed (including failures and skipped checks), plus a "Review" section with the code and security review findings and outcomes. Never put Sick type, notes or secrets in it. End with the PR attribution line from the session reminder.
5. `gh pr create --base main --title "<conventional title>" --body-file <file>`. Verify with `gh pr view --json url,number,state,closingIssuesReferences`.

## 7. Update the board

1. Add the PR to the board if it is not linked: `gh project item-add <n> --owner <owner> --url <pr-url>`.
2. Set the task's Status to `In Review` using the same `item-edit` call as step 2. Do not set `Done`; the merge does that.
3. Confirm assignees are still set on the issue (and on the PR: `gh pr edit --add-assignee @me`).
4. Sub-issues: for each sub-issue the PR actually completes and verified, tick it or close it with a comment linking the PR. Leave the rest open. Base this on test results, not on intent.
5. Re-read the item and confirm Status is `In Review`.

## 8. Report

Keep it short and factual:

- Task: number, title, URL.
- Changes: key files and behavior.
- Tests: each command and its result; anything failing, skipped or not run, with the reason.
- Reviews: code and security review run (or light pass), findings and outcomes.
- Commit hash, branch, PR link.
- Board: Status, assignees, sub-issue progress (n of m).
- Remaining blockers, assumptions and open questions, matching the plan file's "Open items" section (step 5b).

## Rules

- Verify every `gh` operation by reading the state back. If an operation fails, say so and stop or retry sensibly; never fabricate results.
- Pushing, opening a PR and editing the board are outward-facing. The user invoking this skill authorizes them for this one task only.
- Preserve unrelated working-tree changes. No secrets in commits. Follow CLAUDE.md in all cases.
