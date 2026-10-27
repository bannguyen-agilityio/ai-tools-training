"""Test the gates WITHOUT Claude Code.

It pipes the same JSON Claude Code sends on stdin into each hook and checks
whether the hook allowed, asked or blocked.  Run:  python3 test_hooks.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOOKS = ROOT / ".claude" / "hooks"
GATE_VARS = ("RELEASE_APPROVAL", "CHANGE_TICKET", "FIX_MODE")


def run(hook, event, **extra_env):
    env = {k: v for k, v in os.environ.items() if k not in GATE_VARS}
    env.update(extra_env)
    p = subprocess.run([sys.executable, str(HOOKS / hook)],
                       input=json.dumps(event), capture_output=True, text=True, env=env)
    if p.returncode == 2:
        return "block", p.stderr.strip()
    if p.returncode == 0 and '"ask"' in p.stdout:
        return "ask", json.loads(p.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    if p.returncode == 0:
        return "allow", ""
    return f"error({p.returncode})", p.stderr.strip()


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def edit(rel):
    return {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / rel)}}


CASES = [
    # name, expected, hook, event, env
    ("staging deploy",                  "allow", "production_gate.py", bash("python3 deploy.py staging"), {}),
    ("production deploy, no approval",  "block", "production_gate.py", bash("python3 deploy.py production"), {}),
    ("production deploy, approved",     "ask",   "production_gate.py", bash("python3 deploy.py production"), {"RELEASE_APPROVAL": "REL-42"}),
    ("harmless command",                "allow", "production_gate.py", bash("ls"), {}),
    ("edit app code",                   "allow", "protected_paths_gate.py", edit("app/calc.py"), {}),
    ("edit migration, no ticket",       "block", "protected_paths_gate.py", edit("migrations/001_create_users.sql"), {}),
    ("edit migration, with ticket",     "ask",   "protected_paths_gate.py", edit("migrations/001_create_users.sql"), {"CHANGE_TICKET": "CHG-7"}),
    ("edit infra, no ticket",           "block", "protected_paths_gate.py", edit("infra/config.yaml"), {}),
    ("edit test, normal mode",          "allow", "protected_paths_gate.py", edit("tests/test_calc.py"), {}),
    ("edit test, FIX_MODE=1",           "block", "protected_paths_gate.py", edit("tests/test_calc.py"), {"FIX_MODE": "1"}),
]


def main():
    failed = 0
    for name, want, hook, event, env in CASES:
        got, msg = run(hook, event, **env)
        ok = got == want
        failed += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<34} -> {got}" + ("" if ok else f" (want {want})"))
        if "-v" in sys.argv and msg:
            print("        " + msg.replace("\n", "\n        "))
    print(f"\n{len(CASES) - failed}/{len(CASES)} passed. Decisions logged in .claude/gate-audit.log")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
