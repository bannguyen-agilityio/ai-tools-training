---
name: pre-push
description: Code review via sub-agent then push. Mechanical checks (tests, lint, types) are handled by the PreToolUse hook on git push.
user-invocable: true
---

# Pre-Push Review & Push

Code review via sub-agent, then push. Tests, lint, format, and type checks run automatically via the PreToolUse hook when `git push` executes — do not duplicate them here.

## Steps

### 1. Check there is something to push

Run `git status` and `git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -5` to confirm there are unpushed commits. If there is nothing to push, tell the user and stop.

### 2. Code review via sub-agent

Spawn a **code review sub-agent** using the Agent tool:

- Use `subagent_type: "fork"` so it inherits context
- Have it review the diff between the current branch and the base branch (`main` unless the user says otherwise) for correctness bugs, security issues, and logic errors
- The fork should run: `git diff main...HEAD` (or the appropriate base) and review the changes
- Wait for the review result before proceeding

Use this prompt for the fork:

> Review the diff of this branch against main for correctness bugs, security issues, and logic errors. Run `git diff main...HEAD` to get the changes. For each finding, state the file, line, what's wrong, and severity (critical/warning/info). If there are no issues, say "No issues found." Keep the report under 300 words.

If the review finds **critical** issues, report them and stop. Warnings and info items should be reported but do not block the push.

### 3. Push

If no critical review issues were found, ask the user to confirm the push with:

> Review complete — no critical issues. Push to origin?

Only push after the user confirms. Use `git push` (never `--force`). The PreToolUse hook will run tests/lint/types automatically before the push executes.

### Summary

After completion (whether successful or stopped early), give a one-line summary of what happened:
- "Review clean, pushed to origin/<branch>."
- "Stopped: <reason>"
