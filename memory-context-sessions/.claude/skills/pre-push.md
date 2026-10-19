---
name: pre-push
description: Run tests, lint, type-check, and code review before pushing. Use when you want to validate and push your changes.
user_invocable: true
---

# Pre-Push Quality Gate

Run all quality checks and a code review before pushing to remote. Stop at the first failure — do not push broken code.

## Steps

### 1. Check there is something to push

Run `git status` and `git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -5` to confirm there are unpushed commits. If there is nothing to push, tell the user and stop.

### 2. Run unit tests

```bash
uv run pytest
```

If any test fails, report the failures and stop. Do not continue to the next step.

### 3. Run lint and format check

```bash
uv run ruff check . && uv run ruff format --check .
```

If lint or format issues are found, report them and stop. Do not auto-fix — let the user decide.

### 4. Run type check

```bash
uv run pyright
```

If type errors are found, report them and stop.

### 5. Code review via sub-agent

Spawn a **code review sub-agent** using the Agent tool:

- Use `subagent_type: "fork"` so it inherits context
- Have it review the diff between the current branch and the base branch (`main` unless the user says otherwise) for correctness bugs, security issues, and logic errors
- The fork should run: `git diff main...HEAD` (or the appropriate base) and review the changes
- Wait for the review result before proceeding

Use this prompt for the fork:

> Review the diff of this branch against main for correctness bugs, security issues, and logic errors. Run `git diff main...HEAD` to get the changes. For each finding, state the file, line, what's wrong, and severity (critical/warning/info). If there are no issues, say "No issues found." Keep the report under 300 words.

If the review finds **critical** issues, report them and stop. Warnings and info items should be reported but do not block the push.

### 6. Push

If all checks pass and no critical review issues were found, ask the user to confirm the push with:

> All checks passed. Push to origin?

Only push after the user confirms. Use `git push` (never `--force`).

### Summary

After completion (whether successful or stopped early), give a one-line summary of what happened:
- "All checks passed, pushed to origin/<branch>."
- "Stopped at <step>: <reason>"
