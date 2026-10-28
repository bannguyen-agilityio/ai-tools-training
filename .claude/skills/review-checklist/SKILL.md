---
name: review-checklist
description: Use when reviewing a pull request, branch, or diff, or before marking work ready for review. Applies an ordered five-area checklist (correctness, tests, readability, security basics, scope) and produces an evidence-based, read-only review report.
---

# Review Checklist

Review-only skill. Do not modify code, edit tests, commit, push, or merge. Report findings and let the author act.

## 1. Gather context

1. Identify the base branch (PR base, or `main` if unstated) and read the diff: `git diff <base>...HEAD`, plus `git diff --stat` for the file list.
2. Read the ticket or PR description if available (PR text, linked issue, or what the user supplied). If none exists, say so and infer intent only from the diff and commit messages, labelled as an assumption.
3. Read the surrounding code of each changed area: callers, related modules, and existing tests, not just the changed lines.
4. Note the project conventions (existing code style, CLAUDE.md or contributing docs, nearby files) so readability findings are judged against them.

## 2. Review in this order

Finish each area before moving to the next. Prioritize correctness and security over style.

1. **Correctness**: Does the change solve the reported bug and meet the ticket's requirements? Check edge cases, error paths, null/empty input, and callers that might regress.
2. **Tests**: Is there a test for the fix that would fail without the change? Do assertions check specific behavior? Were relevant tests run, and is there evidence (CI output, logs, or your own run)? You may run existing tests if that is safe and needs no installs or config changes; otherwise report them as not run.
3. **Readability**: Is the code understandable and maintainable, and consistent with project conventions? Skip anything a linter or formatter would catch.
4. **Security basics**: Missing authentication or authorization, unsafe input handling (injection, XSS, path traversal), trusting client-supplied values, secrets or sensitive data exposed in code, logs, or responses.
5. **Scope**: Are changes limited to the intended task? Flag unrelated modifications, and changes the task needs but that are missing (docs, migrations, callers, tests).

## 3. Classify every finding

- **Defect**: confirmed by evidence (code you read, a failing test, reproduced behavior). Cite that evidence.
- **Risk**: plausible problem you could not confirm. State what would confirm it.
- **Question**: something needing author clarification.
- **Suggestion**: optional improvement.

Never present a risk or guess as a defect. Do not invent problems or assume behavior without evidence. Report every meaningful, supported finding; there is no minimum or fixed count.

For each actionable finding, give:
- **What**: the issue.
- **Why it matters**: impact.
- **Where**: `path/to/file:line` when available.
- **Fix**: the change that would resolve it (describe it; do not apply it).

## 4. Report format

1. **Summary**: what the change does, in a few sentences.
2. **Findings**: ordered by severity (blocking defects, then risks, questions, suggestions), each with the four fields above.
3. **Checklist results**: one line each for Correctness, Tests, Readability, Security basics, Scope: pass, issues found (refer to findings), or not verified.
4. **Tests and verification**: what you ran or inspected, and what you did not verify. Never claim tests passed without evidence they ran successfully; cite the command or CI result.
5. **Recommendation**: approve, request changes, or needs further investigation, with a brief rationale.

If no actionable problems are found, say so plainly and list the checks you did not perform. Do not claim that this skill enforces CI or branch protection; it is an advisory review only.
