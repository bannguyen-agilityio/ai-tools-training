# LeaveDesk — Requirements & Practice Tasks

> **Two documents:**
> 1. **This file** contains the client brief, the client's answers, and the step-by-step tasks. **Work only from this file.**
> 2. `leavedesk-2-solutions.md` contains reference answers. **Open a section only after** you've committed your own version, then compare.

The project follows the six stages of the *AI-native SDLC playbook*: **Plan → Design → Build → Test → Deploy → Maintain**. Claude drafts, and you review, correct, and decide. Each stage ends with a committed artifact and one number in `docs/metrics.md`.

---

## Part A — Client brief

**Client:** Brightpath Software, a 250-person software company (fictional) in Vietnam.
**Product owner:** Sarah Miller, HR Manager.

**Today's process:** Employees email their manager to ask for leave. The manager replies "OK", and HR updates an Excel file by hand at the end of the month. Emails get lost, balances are often wrong, and nobody knows who is off next week.

**What Sarah said (raw, unedited):**

> "We need a simple internal tool for leave requests. Staff should be able to request leave, managers approve it, and HR can see everything. It should calculate how many days people have left. Public holidays shouldn't count. Something like a team calendar would be great too. We'd like to start using it next month. Budget is limited, so keep it simple."

---

## Part B — Client answer sheet (Sarah's decisions)

**How to use it:** let Claude interview you, and **don't show it this table**. Answer each question from the table. If Claude asks something the table doesn't cover, decide as Sarah would and **add a row**. Afterwards, note which rows Claude never asked about.

| Topic | Sarah's answer |
|---|---|
| Leave types | Annual 12 days/year, Sick 7 days/year (paid), Unpaid (no limit) |
| Half days | Yes, morning or afternoon (0.5 day) |
| What counts | Mon–Fri only; Vietnamese public holidays don't count |
| Public holidays | Vietnamese public holidays, preloaded; HR edits them each year |
| Approver | The employee's direct manager. Managers' own requests go to HR |
| Cancelling | Employee can cancel while *Pending*. Once *Approved*, only HR can cancel; days are refunded |
| Backdating | Sick leave up to 7 days back. Other types must be in the future |
| Overlaps | Not allowed with an existing pending or approved request |
| Notifications | Email to the manager on a new request; to the employee on approve/reject |
| Reject | The manager must give a reason |
| Login | Company email (`@brightpath.com`) + password. SSO later |
| Privacy | Colleagues must not see that someone is on *sick* leave, only that they're off |
| Calendar | Month view of who's off in my team; HR sees all teams |
| Reports | HR needs a monthly export they can open in Excel |
| Devices | Must work in a phone browser. No native app |
| Users | ~250 staff, 16 managers, 2 HR people (owner and deputy) |
| Success | No leave requests by email after launch; HR month-end takes under 10 minutes; no balance corrections |
| Not now | Carry-over of unused days, SSO, Slack, payroll, multi-level approval |
| Deadline | Live next month |

---

## Part C — Practice tasks

### Setup (once)
- [ ] Install Claude Code, Node 20+, Docker, Git, and the GitHub CLI (`gh`).
- [ ] Create a GitHub repo `leavedesk`, and copy this file into it as `docs/REQUIREMENTS.md`, **with Part B removed**. Keep the answer sheet outside the repo (e.g. open in another window), because Claude Code can read any file in the repo. **Do not copy the solutions file into the repo either.**
- [ ] Create `docs/metrics.md` with the table from Part D.

---

### Stage 1 — Plan → `intent.md`
**Hat:** Product owner (Sarah)

1. Create `intent/leave-requests/` on a new branch.
2. Start Claude and run:
   ```
   I'm the HR manager at a 250-person company. Here's my problem: <paste Sarah's message>.
   Interview me like a business analyst — scope, users, constraints, what success looks like —
   one question at a time, until the idea is concrete.
   ```
3. Answer from Part B.
4. Ask Claude to write `intent/leave-management-tool/intent.md` with these sections: Problem, Proposed outcome, Affected users and systems, Constraints, Success measures, Out of scope, Open questions. Keep it under one page.
5. Correct anything Claude got wrong, then commit, open a PR, and merge. **Merging means the intent is accepted.**
6. *(Optional)* Save the intent template as a skill: `.claude/skills/intent-template/SKILL.md`.

**Deliverable:** `intent.md` merged.
**Measure:** time from the first prompt to the merge.
**Compare:** Solutions §1.

---

### Stage 2 — Design → skills + `spec.md`
**Hat:** Product owner, with the tech lead consulted

1. **Write three policy skills**

      Prompt:
      ```
      Do not read or reference any files under @ref/.
      Use @intent/leave-management-tool/intent.md as the source of truth for this task.

      Before creating `spec.md`, analyze the intent document and suggest a set of reusable skills that will help maintain consistency between the requirements and the specification I will define later.

      For each proposed skill, explain:
      1. **Skill name** — a clear, descriptive name.
      2. **Purpose** — what problem or risk the skill addresses.
      3. **Scope** — which requirements, workflows, or design decisions it applies to.
      4. **Rules and guidelines** — what Claude should follow when using this skill.
      5. **Trigger conditions** — when the skill should be activated.
      6. **Consistency checks** — how the skill helps ensure the requirements and specification remain consistent.

      Prioritize cross-cutting concerns such as security, privacy, data integrity, business rules, accessibility, and UX, but only recommend skills that are justified by the intent document.

      Keep the skill set small, focused, and non-overlapping. Explain why each skill should be a reusable skill rather than a one-off requirement in the specification.

      **Important constraints:**
      - Do not create `spec.md` yet.
      - Do not implement any code.
      - Do not invent requirements or business decisions that are not supported by the intent document.
      - Identify ambiguities, missing information, and potential conflicts that should be resolved before writing the specification.
      - Present your proposed skills and rationale for my review and approval before creating any skill files.

      The goal is to establish reusable policies and guidelines first so that the requirements and specification I define later are consistent, complete, and aligned with the agreed product intent.
      ```
   (OPTIONAL) Under `.claude/skills/<name>/SKILL.md`. Each needs frontmatter saying *when* it triggers and a body saying *what to do*.
   - `secure-api`: rules for every API endpoint (authentication, authorization, validation, audit, logging)
   - `hr-privacy`: who may see what (sick leave, reasons, exports)
   - `ux-standard`: mobile, accessibility, form errors, date format, destructive actions
2. **Run the design session** in Claude Code:
   ```
   Read intent/leave-management-tool/intent.md and produce a requirements and design spec.
   Apply the skills available to you so the spec conforms to our security, privacy and UX standards.
   Number every requirement (R1, R2, …) with Given/When/Then acceptance criteria.
   Include: tech stack, data model, API list, screens, how each intent constraint is met, open questions carried forward, and an "Areas of concern" section — especially where policies contradict each other. Save as intent/leave-management-tool/spec.md.
   ```
3. **Review the spec** against the intent:
   - Does it solve the problem?
   - Is every open question answered or carried forward?
   - Is every rule in Part B covered by an acceptance criterion?
4. **Resolve every area of concern** and write each decision into the spec.
5. *(Optional)* Have Claude mock up 4 screens (Dashboard, New Request, Approvals, Calendar) and save them in `intent/leave-management-tool/mocks/`.
6. Commit `spec.md` in a PR and merge it. **Merging means you've decided to build.**

**Deliverable:** 3 skills + `spec.md` merged.
**Measure:** time between the `intent.md` merge and the `spec.md` merge.
**Compare:** Solutions §2 (skills) and §3 (requirements, data model, API, concerns). For each difference, note whether it's *better, worse, or just different*. Keep what's better, and write down why.

---

### Stage 3 — Build
**Hat:** Engineer

1. **Scaffold** the stack you chose in the spec, then run `/init` in Claude. Cut the result down to a **one-page `CLAUDE.md`** with Commands, Conventions, Architecture, "Verifying your work", and "Things Claude gets wrong". Commit it.
   **Rule:** when Claude makes the same mistake twice, the correction goes into `CLAUDE.md`.
2. **Plan mode for every change.** Press Shift+Tab until you're in plan mode, then:
   ```
   Read intent/leave-requests/intent.md and spec.md. Produce an implementation plan for <R-numbers>:
   files that change, order of work, risks, and the tests that prove each acceptance criterion.
   ```
   Push back at least twice: *What could this break? Which step is riskiest? What alternatives did you reject?*
   Iterate until **someone who never saw the conversation could implement it**, then commit the plan as `intent/leave-requests/plan-<R-numbers>.md`.
3. **Add hooks** in `.claude/settings.json` that **block**:
   - edits to `.env*` and to migrations that were already applied
   - edits to test files while you're in "fix mode"
   - any route file that has no authentication or that logs sensitive fields (run a `check:api` script after each edit)

   Run the same `check:api` script as a required PR check too.
4. **Add a `verifier` subagent** in `.claude/agents/verifier.md`. It runs the app, exercises the change as each role, and reports mismatches with the plan. It reports only and doesn't fix anything.
5. **Build in waves**, using parallel worktrees for tasks that touch different files:
   ```bash
   claude --worktree <task-a>    # terminal 1
   claude --worktree <task-b>    # terminal 2
   ```
   Decide the waves yourself from your plans, starting with 2–3 parallel sessions at most.
6. **One PR per plan.** The title cites R-numbers, and the body links the plan and pastes the test output.

**Deliverable:** `CLAUDE.md`, hooks, verifier, and all requirements merged.
**Measure:** share of PRs merged from the first implementation pass, and repeated mistakes.
**Compare:** Solutions §4 (CLAUDE.md, plan, hooks, waves).

---

### Stage 4 — Test
**Hat:** QA / Engineer

1. **Feedback loop:** make sure there's one command each for tests, E2E, lint and type check, and that each exits non-zero on failure. Give Claude measurable targets ("all tests in X pass"). For UI work, let Claude screenshot the page and compare it to the mock.
2. **Test matrix:** write `docs/test-cases.md` with one row per acceptance criterion, plus **at least 8 edge cases you come up with yourself**.
3. **Plant and fix these bugs, test first:**
   - A Fri→Mon request counts 4 days instead of 2.
   - Rejecting a request doesn't refund the reserved days.
   - A manager can approve another team's request through the API.

   For each one: Claude writes a failing test → you confirm it fails for the right reason → commit → turn on fix mode (`touch .claude/fix-mode`) → Claude fixes the code without editing the test.
4. **Evals in CI:** turn 5 real tasks from your merged PRs into evals (start commit + prompt + checks). Add a workflow that runs them on PRs touching `CLAUDE.md`, `.claude/**` or `evals/**`, and nightly.
5. **Test your guardrails:** delete an important line from `CLAUDE.md` and confirm an eval fails, then restore it.

**Deliverable:** test matrix, 3 bugs fixed test-first, eval suite running.
**Measure:** first-pass CI success rate and eval pass rate.
**Compare:** Solutions §5 (edge cases, eval examples).

---

### Stage 5 — Deploy
**Hat:** Tech lead → Release manager

1. Write a **`REVIEW.md`** with three review passes (Bugs, Security, Compliance with spec and plan), what counts as *Important* vs *Nit*, a cap on the number of nits, and what not to report.
2. Turn on **Claude code review** on PRs, either the managed service or `claude-code-action`. Set **branch protection** so a human must approve. Practise tagging `@claude` on a comment so it pushes a fix.
3. **CI with Claude:** add a step that triages failed builds with `claude -p`. Agent jobs get no production credentials.
4. **Environment tiers:** preview deploys are automatic, staging deploys from `main`, and production needs approval. Make **rollback one command** and rehearse it on staging.
5. **Release gate hook:** block `deploy:prod` unless an approval record from the release manager exists, and make sure the agent can't write that record.
6. Do an **acceptance walk-through as Sarah** on staging, covering every R-number. Each gap becomes a new `intent.md`.
7. Have Claude draft the **release notes** (for HR and staff, not developers) and a one-page **user guide** per role. Then approve, tag `v1.0.0`, and release.

**Deliverable:** AI review + human approval working, gate working, v1.0.0 live.
**Measure:** time to first review, and time spent waiting at the gate.
**Compare:** Solutions §6 (REVIEW.md, CI step, gate design).

---

### Stage 6 — Maintain
**Hat:** Service owner

1. Pick **one metric** with a stable baseline (e.g. the error rate when submitting requests, the CI failure rate, or requests stuck in Pending for more than 3 days).
2. Write a **deterministic detection script** (mean + σ over 30 days, plus drift rules), and unit-test it. No AI is used in detection.
3. Define **response tiers** in `ops/bands.yaml`: 1σ log only, 2σ read-only diagnosis, 3σ PR or the pre-approved rollback only.
4. Set up an **hourly scheduled job** that runs `claude -p` with only that tier's tools. Claude writes its findings as a new `intent.md`.
5. **Rehearse an incident:** plant a regression, watch the breach, the rollback and the new `intent.md`, then triage it (fix / schedule / dismiss), fix it, and **add an eval for it**.

**Deliverable:** one full loop, from breach to rollback to `intent.md` to fix to new eval.
**Measure:** time from breach to `intent.md`.
**Compare:** Solutions §7.

---

## Part D — Metrics log template (`docs/metrics.md`)

| Stage | Leading indicator | Value | Lagging indicator | Value |
|---|---|---|---|---|
| Plan | First prompt → intent merged | | Intents accepted vs closed | |
| Design | Intent → spec merged | | Spec changes after the first plan | |
| Build | First-pass merge rate | | Rework cycles per PR | |
| Test | First-pass CI success / eval pass rate | | Bugs found after merge | |
| Deploy | Time to first review / gate wait | | Defects caught before vs after merge | |
| Maintain | Breach → intent.md | | Repeat incidents | |

## Final checklist
- [ ] intent → spec → plan chain committed, with PRs citing R-numbers
- [ ] `CLAUDE.md` (≤ 1 page), 3 skills, 2+ hooks, verifier, `REVIEW.md`
- [ ] All requirements merged through AI review + human approval, CI green
- [ ] ≥ 5 evals running on config changes and nightly
- [ ] v1.0.0 released through the gate; rollback rehearsed
- [ ] One incident rehearsed end to end
- [ ] Metrics log filled in, and a comparison note with the solutions for each stage

## Stretch (v1.1, run through all six stages again)
Carry-over of up to 6 annual days (expiring 31 Dec of the following year) · Google SSO · Slack notification to managers · Pro-rated quota for people who join mid-year
