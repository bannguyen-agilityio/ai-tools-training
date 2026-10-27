# hooks-gate-lab

Practice project for the Claude Academy lesson **"Hooks as approval gates"**
(The AI-Native SDLC Playbook, Stage 5: Deploy).

Pure Python 3, no dependencies. Designed to live as a **sub-folder** of a bigger repo.

## What's inside

```
hooks-gate-lab/
├── .claude/
│   ├── settings.json              # registers the hooks (PreToolUse)
│   └── hooks/
│       ├── gate.py                # helpers: allow / ask / block + audit log
│       ├── production_gate.py     # GATE 1: production deploy needs RELEASE_APPROVAL
│       └── protected_paths_gate.py# GATE 2: migrations/ infra/ need CHANGE_TICKET; tests/ locked in FIX_MODE
├── app/calc.py                    # tiny app with a deliberate bug
├── tests/test_calc.py             # unittest (one test fails on purpose)
├── migrations/  infra/            # protected paths
├── deploy.py                      # fake deploy (only prints)
├── test_hooks.py                  # test the gates without Claude Code
└── managed/managed-settings.example.json   # reference for Exercise 5
```

## The three decisions a hook can make

| Decision | How the hook says it | What happens |
|---|---|---|
| allow | exit 0, no output | normal permission flow |
| ask   | exit 0 + JSON `permissionDecision: "ask"` | Claude Code pauses; **you** approve or reject |
| block | exit 2 + message on stderr | action stopped; Claude sees the reason + route to approval |

Every decision is written to `.claude/gate-audit.log` with a timestamp.

## ⚠️ Running as a sub-project

Claude Code loads `.claude/settings.json` from the folder you **start it in**
(`$CLAUDE_PROJECT_DIR`). So:

```bash
cd your-repo/hooks-gate-lab
claude
```

If you start `claude` from the parent repo root, these hooks will **not** load.
(Windows: if `python3` isn't found, change it to `python` or `py` in `settings.json`.)

## Step 0 — check without Claude

```bash
python3 test_hooks.py        # 10/10 should pass
python3 test_hooks.py -v     # also show the messages Claude would see
python3 -m unittest          # 1 test fails on purpose (Exercise 3)
```

## Exercises

**1. Block (no approval).** Start `claude` in this folder and ask:
> Deploy the app to production with deploy.py

Expected: blocked, and Claude tells you to get a `REL-####`. Check `.claude/gate-audit.log`.
Also ask it to deploy to **staging** — it should be allowed.

**2. Ask (with approval).** Restart with an authorization:
```bash
RELEASE_APPROVAL=REL-1234 claude
```
Ask for the production deploy again. Claude Code should now **pause and ask you**,
showing the reason. Try approving once and rejecting once.

**3. Protected test files.** Run `FIX_MODE=1 claude` and ask:
> The tests are failing, make them pass.

Expected: any attempt to edit `tests/` is blocked; Claude must fix `app/calc.py` instead.

**4. Protected paths.** Ask Claude to add a `name` column in `migrations/001_create_users.sql`.
Blocked without a ticket → retry with `CHANGE_TICKET=CHG-99 claude` → it asks.

**5. Write your own gate (homework).**
- a) Block `git push` to `main` unless `MERGE_APPROVAL` is set. Add cases to `test_hooks.py` first, then the hook.
- b) Gates are dumb string matches. Try to sneak past Gate 1 (e.g. `python3 deploy.py prod`). Harden it.
- c) Read `managed/managed-settings.example.json`: why does `allowManagedHooksOnly` mean your
  project `settings.json` gate would stop running, and where must the gate move?

## Measure (from the lesson)

- Leading: time waiting on each gate → compare ASK timestamps in the audit log.
- Lagging: violations that reached "production" before vs. after the gates.
