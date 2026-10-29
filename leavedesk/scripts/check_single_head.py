"""Fail if Alembic has more than one head (two branches merged without a merge revision)."""

import sys

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    heads = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    if len(heads) != 1:
        print(f"expected exactly one Alembic head, found {len(heads)}: {', '.join(heads)}")
        return 1
    print(f"single Alembic head: {heads[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
