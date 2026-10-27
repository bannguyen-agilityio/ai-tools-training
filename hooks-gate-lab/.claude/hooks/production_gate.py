"""GATE 1 - Release authorization (Stage 5: Deploy).

  production deploy, no RELEASE_APPROVAL  -> BLOCK, explain how to get approval
  production deploy, RELEASE_APPROVAL set -> ASK, the person in the session confirms
  anything else                           -> ALLOW
"""
from gate import allow, ask, block, env, read_event

GATE = "production-gate"

event = read_event()
cmd = event.get("tool_input", {}).get("command", "")

if "deploy" in cmd and "production" in cmd:
    approval = env("RELEASE_APPROVAL")
    if not approval:
        block(GATE, cmd,
              "BLOCKED by production-gate: production deploys need a release authorization.\n"
              "Route to approval: get a REL-#### id from the release manager, then restart with\n"
              "  RELEASE_APPROVAL=REL-1234 claude")
    ask(GATE, f"{cmd} [{approval}]",
        f"Production deploy under release authorization {approval}. Approve?")

allow(GATE, cmd)
