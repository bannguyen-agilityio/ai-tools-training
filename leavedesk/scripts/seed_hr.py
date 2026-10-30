"""Create the first HR admin (there is no sign-up; HR invites everyone else).

    MIGRATION_DATABASE_URL=postgresql://owner... uv run python scripts/seed_hr.py <email> "<Name>"

The password is read from SEED_HR_PASSWORD or prompted for (>= 12 characters). Additive and
idempotent: an existing employee with that email is left untouched. Run as the owner role.
"""

import getpass
import os
import sys
from datetime import date

import psycopg

from app.modules.auth.passwords import hash_password


def main(email: str, name: str) -> None:
    if not email.endswith("@asnet.com.vn"):
        sys.exit("Email must end with @asnet.com.vn (R1).")
    password = os.environ.get("SEED_HR_PASSWORD") or getpass.getpass("Password (min 12): ")
    if len(password) < 12:
        sys.exit("Password must be at least 12 characters (R2).")
    url = os.environ["MIGRATION_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    year = date.today().year
    with psycopg.connect(url) as c:
        if c.execute("SELECT 1 FROM employee WHERE lower(email) = lower(%s)", (email,)).fetchone():
            sys.exit(f"{email} already exists; nothing changed.")
        row = c.execute(
            "INSERT INTO employee (name, email, role, start_date) VALUES (%s,%s,'hr',%s)"
            " RETURNING id",
            (name, email, f"{year - 1}-01-01"),
        ).fetchone()
        assert row is not None
        c.execute(
            "INSERT INTO user_identity (employee_id, provider, password_hash)"
            " VALUES (%s,'password',%s)",
            (row[0], hash_password(password)),
        )
        for typ, days in (("annual", 12), ("sick", 7)):
            c.execute(
                "INSERT INTO balance_entry (employee_id, leave_type_code, leave_year, kind, days)"
                " VALUES (%s,%s,%s,'entitlement',%s)",
                (row[0], typ, year, days),
            )
    print(f"created HR admin {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
