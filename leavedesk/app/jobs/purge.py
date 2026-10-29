"""Daily job: python -m app.jobs.purge. Idempotent (spec 5.6)."""

import asyncio
from datetime import UTC, datetime

from app.core.db import get_session_factory
from app.modules.auth.purge import purge


async def run() -> dict[str, int]:
    async with get_session_factory()() as db:
        return await purge(db, datetime.now(UTC))


def main() -> None:
    print(f"purge: deleted {asyncio.run(run())}")


if __name__ == "__main__":
    main()
