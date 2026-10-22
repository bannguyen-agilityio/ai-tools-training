# Format-on-edit hook

Formats JS/TS files with the repo's Prettier (`.prettierrc`, `prettier@3.6.2`) after Claude edits them.

- **Events:** `PreToolUse` and `PostToolUse`, matcher `Edit|Write` (see `.claude/settings.json`).
- **Input:** hook JSON on stdin; the target is `tool_input.file_path`.
- **Scope:** `.ts .tsx .js .jsx .mjs .cjs .mts .cts` inside the project; skips `node_modules`, `dist`, `coverage`, `data`, `prisma/migrations`.
- **No loops:** Prettier runs as a child process (not a Claude tool call), so it cannot re-trigger the hook, and it is skipped when the file is already formatted.
- **Your changes are safe:** `pre` records whether the file is already Prettier-clean (or new). `post` formats only those files, so a file you left unformatted is never reformatted wholesale.

## Setup

1. `npm ci` (installs Prettier; the hook skips with a warning if it is missing).
2. Start Claude Code **from `mini-ecommerce-app/`** so `.claude/settings.json` is picked up, and approve the hooks if prompted. Check with `/hooks`.

## Testing

Simulate the events without Claude (from `mini-ecommerce-app/`):

```bash
export CLAUDE_PROJECT_DIR=$PWD
f=src/hooktest.ts; ev="{\"session_id\":\"t\",\"tool_input\":{\"file_path\":\"$f\"}}"
printf 'export const a = 1;\n' > $f && git add -N $f
echo "$ev" | node .claude/hooks/format.mjs pre
printf 'export const a = 1;\nexport   const b   =  {x:1}\n' > $f
echo "$ev" | node .claude/hooks/format.mjs post
git diff $f          # expect: `export const b = { x: 1 };`
git rm -q --cached $f; rm $f
```

Also verify: an already-unformatted file is left untouched, and files under `node_modules/` are ignored.

# Block force-push hook

`block-force-push.mjs` is a `PreToolUse` hook (matcher `Bash`). It denies `git push --force`, `--force-with-lease`, `--force-if-includes`, `-f` (also inside clusters such as `-fu`), `--mirror` and `+refspec` pushes, including abbreviated flags (`--forc`), after `&&`, `;`, `|`, with `git -C "a dir"`, behind wrappers (`sudo`, `env`, `xargs`...), and inside `bash -c`, `eval`, `$(...)` and `(...)`. It cannot see through variables, aliases or scripts that call git internally. It answers with the documented JSON `hookSpecificOutput.permissionDecision: "deny"` plus a reason Claude sees. Plain `git push`, `echo "git push --force"` and `git fetch --force` are allowed. The script only parses the command string; it never runs anything.

Test (safe, runs no git commands): `node --test .claude/hooks/block-force-push.test.mjs`

## If the rule is too broad

- **Disable temporarily:** run `/hooks` and turn it off, or set `"disableAllHooks": true` in `.claude/settings.local.json` (git-ignored by convention; remove it later). This also disables the format hook.
- **Disable permanently:** delete the `block-force-push.mjs` entry (the `Bash` matcher block) from `.claude/settings.json`.
- **Recover a blocked legitimate push:** run it yourself in your terminal (or via `! git push ...` in the prompt); hooks only gate Claude's tool calls. Then fix the pattern in `isForcePush` and add a case to the test file.
- **Hook crashes:** a non-zero exit other than 2 is non-blocking, so a broken script never wedges Claude; fix or remove it.

# Completion notification hook

`notify.mjs` is a `Stop` hook (fires when Claude finishes responding). It rings the terminal bell, then tries a desktop notification: `osascript` on macOS, a Windows toast via `powershell.exe` on WSL, `notify-send` on Linux. All steps are best-effort and failures are ignored, so it never blocks Claude.

Test: `echo '{}' | CLAUDE_PROJECT_DIR=$PWD node .claude/hooks/notify.mjs`

Remove it by deleting the `Stop` entry from `.claude/settings.json`.
