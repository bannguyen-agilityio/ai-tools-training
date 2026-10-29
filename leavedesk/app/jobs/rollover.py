"""1 Jan job: python -m app.jobs.rollover [YEAR]. Idempotent (spec 5.6)."""

import asyncio
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.modules.balances import service


async def run(year: int) -> int:
    async with get_session_factory()() as db:
        return await service.rollover(db, year)


def resolve_year(argv: list[str], current_year: int) -> int:
    """The target year: argv[0] or the current company-timezone year. Never a future year,
    so a stray run cannot roll balances before the year has ended."""
    year = int(argv[0]) if argv else current_year
    if year > current_year:
        raise ValueError(f"cannot roll over into {year}: it is after {current_year}")
    return year


def main(argv: list[str]) -> None:
    now = datetime.now(ZoneInfo(get_settings().company_tz))
    year = resolve_year(argv, now.year)
    print(f"rollover {year}: wrote {asyncio.run(run(year))} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
