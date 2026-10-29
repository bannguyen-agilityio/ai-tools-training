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


def main(argv: list[str]) -> None:
    year = int(argv[0]) if argv else datetime.now(ZoneInfo(get_settings().company_tz)).year
    print(f"rollover {year}: wrote {asyncio.run(run(year))} entries")


if __name__ == "__main__":
    main(sys.argv[1:])
