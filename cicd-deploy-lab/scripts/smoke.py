"""Post-deploy smoke check. Exit 1 if the record is missing or unhealthy."""
import json
import sys
from pathlib import Path

env = sys.argv[1]
p = Path(f"deploy-{env}.json")
if not p.exists():
    sys.exit(f"no deploy record for {env}")
rec = json.loads(p.read_text())
print(rec)
sys.exit(0 if rec.get("status") == "ok" else 1)
