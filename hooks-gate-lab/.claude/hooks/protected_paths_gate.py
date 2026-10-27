"""GATE 2 - Protected paths (Stage 3: Build / Stage 4: Test).

  migrations/ or infra/, no CHANGE_TICKET  -> BLOCK
  migrations/ or infra/, CHANGE_TICKET set -> ASK
  tests/ while FIX_MODE=1                  -> BLOCK (fix the code, not the tests)
  anything else                            -> ALLOW
"""
from pathlib import Path

from gate import LAB_ROOT, allow, ask, block, env, read_event

GATE = "protected-paths"
PROTECTED = ("migrations", "infra")

event = read_event()
file_path = event.get("tool_input", {}).get("file_path", "")

try:
    rel = Path(file_path).resolve().relative_to(LAB_ROOT)
except ValueError:
    allow(GATE, file_path)  # outside this lab -> not our business

top = rel.parts[0] if rel.parts else ""
rel_str = rel.as_posix()

if top in PROTECTED:
    ticket = env("CHANGE_TICKET")
    if not ticket:
        block(GATE, rel_str,
              f"BLOCKED by protected-paths: {rel_str} is a protected path ({'/'.join(PROTECTED)}).\n"
              "Route to approval: open a change ticket, then restart with\n"
              "  CHANGE_TICKET=CHG-1234 claude")
    ask(GATE, f"{rel_str} [{ticket}]",
        f"Editing protected path {rel_str} under change ticket {ticket}. Approve?")

if top == "tests" and env("FIX_MODE") == "1":
    block(GATE, rel_str,
          "BLOCKED by protected-paths: tests are read-only during a fix task (FIX_MODE=1).\n"
          "Fix the code in app/ so the existing tests pass.")

allow(GATE, rel_str)
