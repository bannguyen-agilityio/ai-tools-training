"""Daily job: python -m app.jobs.expire_carry. Idempotent (spec 5.6)."""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.modules.balances import service


async def run() -> int:
    today = datetime.now(ZoneInfo(get_settings().company_tz)).date()
    async with get_session_factory()() as db:
        return await service.expire_carry(db, today)


def main() -> None:
    print(f"expire_carry: wrote {asyncio.run(run())} entries")


if __name__ == "__main__":
    main()
