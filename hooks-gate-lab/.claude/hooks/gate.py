"""Shared helpers for the approval-gate hooks.

A PreToolUse hook receives the tool call as JSON on stdin and decides:
  allow -> exit 0, no output (normal permission flow continues)
  ask   -> exit 0, print JSON with permissionDecision "ask" (a human must confirm)
  block -> exit 2, reason on stderr (Claude sees the reason and stops)

Every decision is appended to .claude/gate-audit.log (the "governance" part).
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Folder that holds .claude/ -> the lab root. Works even when this lab is a
# sub-folder inside a bigger repo, because it does not rely on the cwd.
LAB_ROOT = Path(__file__).resolve().parents[2]
AUDIT_LOG = LAB_ROOT / ".claude" / "gate-audit.log"


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def _audit(gate: str, verdict: str, detail: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{gate}\t{verdict}\t{detail}\n")


def allow(gate: str, detail: str) -> None:
    _audit(gate, "ALLOW", detail)
    sys.exit(0)


def ask(gate: str, detail: str, reason: str) -> None:
    _audit(gate, "ASK", detail)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def block(gate: str, detail: str, message: str) -> None:
    _audit(gate, "BLOCK", detail)
    print(message, file=sys.stderr)
    sys.exit(2)


def env(name: str) -> str:
    return os.environ.get(name, "").strip()
