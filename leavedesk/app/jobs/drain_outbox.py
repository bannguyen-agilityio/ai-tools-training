"""Send due email_outbox rows: `python -m app.jobs.drain_outbox` (CI backstop), or in-process."""

import asyncio
import logging

from app.core.db import get_session_factory
from app.modules.email.factory import get_sender
from app.modules.email.outbox_service import drain_due

log = logging.getLogger("app.jobs.drain_outbox")
INTERVAL_SECONDS = 60


async def run_once() -> int:
    async with get_session_factory()() as db:
        return await drain_due(db, get_sender())


async def run_forever() -> None:
    """In-process loop started from the app lifespan (A-28)."""
    while True:
        try:
            await run_once()
        except Exception as exc:
            # Type only: exception text can carry mail content.
            log.error("outbox drain failed: %s", type(exc).__name__)
        await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    from app.core.logging import configure_logging

    configure_logging()
    asyncio.run(run_once())
