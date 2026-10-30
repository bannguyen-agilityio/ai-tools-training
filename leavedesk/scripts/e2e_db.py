"""Local Playwright support (never for staging or production).

    E2E_DATABASE_URL=postgresql+psycopg://... uv run python scripts/e2e_db.py seed
    E2E_DATABASE_URL=... uv run python scripts/e2e_db.py outbox <email>   # JSON, newest first
    E2E_DATABASE_URL=... uv run python scripts/e2e_db.py sql "<statement>"  # owner SQL, JSON rows

`seed` wipes the people tables and recreates the personas in `e2e/personas.ts`. All use the
password PASSWORD. The URL must be an owner URL for a throwaway database.
"""

import json
import os
import sys
import uuid
from datetime import date
from urllib.parse import urlsplit

import psycopg

from app.modules.auth.passwords import hash_password

PASSWORD = "Correct-Horse-Battery-9"
YEAR = date.today().year

# key, name, role, manager key, team, deputy
PEOPLE = [
    ("hr1", "Hana HR", "hr", None, None, False),
    ("hr2", "Hugo HR", "hr", None, None, False),
    ("deputy", "Dana Deputy", "employee", None, None, True),
    ("mgr1", "Mia Manager", "manager", None, "Alpha", False),
    ("mgr2", "Max Manager", "manager", None, "Beta", False),
    ("emp1", "Eli Employee", "employee", "mgr1", "Alpha", False),
    ("emp2", "Eva Employee", "employee", "mgr1", "Alpha", False),
    ("emp3", "Ian Employee", "employee", "mgr2", "Beta", False),
    ("orphan", "Olga Orphan", "employee", None, None, False),
]


def url() -> str:
    raw = os.environ["E2E_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    name = urlsplit(raw).path.rsplit("/", 1)[-1]
    if not name.endswith("_e2e"):
        sys.exit("Refusing: E2E_DATABASE_URL must point at a database whose name ends in '_e2e'.")
    return raw


def seed() -> None:
    pw_hash = hash_password(PASSWORD)
    with psycopg.connect(url(), autocommit=True) as c:
        # TRUNCATE employee CASCADE also empties public_holiday (created_by FK): keep the seed.
        # Kept in a real table, not a temp one, so a failed run cannot lose the migration's seed.
        c.execute("CREATE SCHEMA IF NOT EXISTS e2e_keep")
        c.execute(
            "CREATE TABLE IF NOT EXISTS e2e_keep.holiday AS"
            " SELECT * FROM public_holiday WHERE source = 'seed'"
        )
        c.execute(
            "TRUNCATE email_outbox, notification, audit_log, session, login_attempt, "
            "one_time_token, user_identity, balance_entry, leave_request_day, leave_request, "
            "team, employee CASCADE"
        )
        c.execute("UPDATE e2e_keep.holiday SET created_by = NULL")
        c.execute("INSERT INTO public_holiday SELECT * FROM e2e_keep.holiday")
        ids: dict[str, uuid.UUID] = {k: uuid.uuid4() for k, *_ in PEOPLE}
        teams = {t: uuid.uuid4() for t in ("Alpha", "Beta")}
        for t, tid in teams.items():
            c.execute("INSERT INTO team (id, name) VALUES (%s, %s)", (tid, t))
        for key, name, role, mgr, team, deputy in PEOPLE:
            c.execute(
                "INSERT INTO employee (id, name, email, role, is_hr_deputy, team_id, manager_id,"
                " start_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    ids[key],
                    name,
                    f"{key}@asnet.com.vn",
                    role,
                    deputy,
                    teams.get(team) if team else None,
                    ids[mgr] if mgr else None,
                    f"{YEAR - 1}-01-01",
                ),  # fmt: skip
            )
            c.execute(
                "INSERT INTO user_identity (employee_id, provider, password_hash)"
                " VALUES (%s,'password',%s)",
                (ids[key], pw_hash),
            )
            for typ, days in (("annual", 12), ("sick", 7)):
                c.execute(
                    "INSERT INTO balance_entry (employee_id, leave_type_code, leave_year, kind,"
                    " days) VALUES (%s,%s,%s,'entitlement',%s)",
                    (ids[key], typ, YEAR, days),
                )
        for key, team_name in (("mgr1", "Alpha"), ("mgr2", "Beta")):
            c.execute("UPDATE team SET manager_id=%s WHERE name=%s", (ids[key], team_name))
        # Carried days for emp2, so the Dashboard shows an expiry.
        c.execute(
            "INSERT INTO balance_entry (employee_id, leave_type_code, leave_year, kind, days,"
            " expires_on) VALUES (%s,'annual',%s,'carry_over',3,%s)",
            (ids["emp2"], YEAR, f"{YEAR}-12-31"),
        )
    print(f"seeded {len(PEOPLE)} people; password {PASSWORD}")


def rows(sql: str, params: tuple[object, ...] = ()) -> None:
    with psycopg.connect(url(), autocommit=True) as c:
        cur = c.execute(sql, params or None)
        cols = [d.name for d in cur.description or []]
        out = [dict(zip(cols, r, strict=True)) for r in cur.fetchall()] if cols else []
    print(json.dumps(out, default=str))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "seed":
        seed()
    elif cmd == "outbox":
        rows(
            "SELECT template, subject, body, status, created_at FROM email_outbox"
            " WHERE to_address = %s ORDER BY created_at DESC",
            (sys.argv[2],),
        )
    elif cmd == "sql":
        rows(sys.argv[2])
    else:
        sys.exit(__doc__)
