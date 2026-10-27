"""Fake deploy. Only prints and writes a deploy record.

Usage: python3 scripts/deploy.py staging|production [--dry-run]
Verifies the smoke check first and refuses to deploy if it fails.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.version import health

env = sys.argv[1] if len(sys.argv) > 1 else "staging"
dry = "--dry-run" in sys.argv
if env not in ("staging", "production"):
    sys.exit(f"unknown environment: {env}")

h = health()
if h["status"] != "ok":
    sys.exit("smoke check failed - aborting deploy")

print(f"(pretend) deploying {h['version']} to {env}{' [dry-run]' if dry else ''} ...")
if not dry:
    time.sleep(1)
    Path(f"deploy-{env}.json").write_text(json.dumps({"env": env, **h, "at": time.time()}))
print(f"done: {env}")
