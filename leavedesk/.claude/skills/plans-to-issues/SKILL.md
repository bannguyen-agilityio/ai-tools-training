---
name: plans-to-issues
description: Creates a GitHub issue for each plan file in specs/<NNN>-*/plans/ and adds them to a GitHub Project board, creating the board if needed. Use when the user asks to publish, sync, or track plans as GitHub issues or on a project board.
---

Turns plan Markdown files into tracked GitHub issues. Never edits plan files or application code.

## 1. Preflight

1. Locate `specs/<NNN>-<name>/plans/` (the folder the user names; if only one spec exists, use it). Run all commands from the repo root.
2. `gh auth status`. Project commands need the `project` and `read:project` scopes. If missing, stop and ask the user to run `! gh auth refresh -s project,read:project` (it is interactive; you cannot do it).
3. Get the repo and owner: `gh repo view --json nameWithOwner,owner`.

## 2. Find the board

1. `gh project list --owner <owner> --format json`. Reuse a board titled "LeaveDesk" (or the title the user gives).
2. If none exists, `gh project create --owner <owner> --title "LeaveDesk"`. Report its URL.

## 3. Avoid duplicates

1. `gh issue list --state all --limit 200 --json title,number`.
2. Skip any plan whose title already exists as an issue. Report the skipped ones. Never recreate or edit existing issues unless asked.

## 4. Create the issues

For every `*.md` in the plans folder, including `README.md`:

```bash
for f in *.md; do
  t=$(head -1 "$f" | sed 's/^# *//')
  gh issue create --title "$t" --body-file "$f" --project "LeaveDesk"
done
```

- Title is the first heading with `# ` removed. Body is the file's full content, unmodified.
- `--project` adds the issue to the board in the same call.
- Do not add labels, assignees or milestones unless the user asks.

## 5. Verify and report

1. `gh project view <number> --owner <owner> --format json` and check `items.totalCount` equals the board's earlier count plus the issues created.
2. Report: board URL, issue range or list, skipped duplicates, and any failures. Count files from the directory listing, not from memory.

## Rules

- Issue bodies come from plans only, so they follow `CLAUDE.md` privacy rules already. Do not add content from `ref/` (never read it).
- Creating a board and issues is outward-facing. If the user did not clearly ask for it, confirm first.
