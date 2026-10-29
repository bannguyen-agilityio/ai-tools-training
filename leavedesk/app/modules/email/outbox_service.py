import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.email.outbox_models import EmailOutbox
from app.modules.email.sender import EmailSender, SendError

log = logging.getLogger("app.email")

# Wait after the Nth failed attempt (R26). A 5th failure marks the mail `failed`, so the last
# step is only reached if MAX_ATTEMPTS is raised.
BACKOFF = (
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(hours=12),
)
MAX_ATTEMPTS = 5
BATCH = 50


async def drain_due(db: AsyncSession, sender: EmailSender, now: datetime | None = None) -> int:
    """Send due pending mail. Commits per row. Returns the number of rows attempted."""
    now = now or datetime.now(UTC)
    attempted = 0
    # One row per transaction: the lock is held only for the row being sent, so two drainers
    # (in-process loop and the CI backstop) never send the same mail twice.
    while attempted < BATCH:
        row = await db.scalar(
            select(EmailOutbox)
            .where(EmailOutbox.status == "pending", EmailOutbox.next_try_at <= now)
            .order_by(EmailOutbox.next_try_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if row is None:
            break
        attempted += 1
        try:
            await sender.send(to=row.to_address, subject=row.subject, body=row.body)
        except SendError as exc:
            row.attempts += 1
            row.last_error = str(exc.code) if exc.code is not None else "network"
            if row.attempts >= MAX_ATTEMPTS:
                row.status = "failed"
                log.warning("email %s failed after %s attempts", row.id, row.attempts)
            else:
                row.next_try_at = now + BACKOFF[row.attempts - 1]
        else:
            row.status = "sent"
            row.sent_at = now
            row.last_error = None
        await db.commit()
    return attempted


async def list_failed(db: AsyncSession) -> list[EmailOutbox]:
    result = await db.scalars(
        select(EmailOutbox).where(EmailOutbox.status == "failed").order_by(EmailOutbox.created_at)
    )
    return list(result)


async def retry(db: AsyncSession, *, actor_id: uuid.UUID, outbox_id: uuid.UUID) -> EmailOutbox:
    row = await db.get(EmailOutbox, outbox_id, with_for_update=True)
    if row is None:
        raise ProblemError(404, "Email not found")
    if row.status != "failed":
        raise ProblemError(409, "Only failed emails can be retried")
    row.status = "pending"
    row.attempts = 0
    row.next_try_at = datetime.now(UTC)
    await audit.record(
        db,
        actor_id=actor_id,
        action="email.retry",
        target_type="email_outbox",
        target_id=str(row.id),
    )
    await db.commit()
    return row
