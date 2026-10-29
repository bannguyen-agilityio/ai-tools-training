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
LINK_TEMPLATES = frozenset({"invite", "password_reset"})
BATCH = 50


async def drain_due(db: AsyncSession, sender: EmailSender, now: datetime | None = None) -> int:
    """Send due pending mail. Commits per row. Returns the number of rows attempted."""
    fixed_now = now  # tests pass a clock; in production each row is stamped at its own time
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
        except Exception as exc:
            # Any failure counts as an attempt, so one bad row cannot block the queue.
            stamp = fixed_now or datetime.now(UTC)
            row.attempts += 1
            code = exc.code if isinstance(exc, SendError) else None
            row.last_error = str(code) if code is not None else type(exc).__name__
            if row.attempts >= MAX_ATTEMPTS:
                row.status = "failed"
                _drop_link(row)
                log.warning("email %s failed after %s attempts", row.id, row.attempts)
            else:
                row.next_try_at = stamp + BACKOFF[row.attempts - 1]
        else:
            row.status = "sent"
            row.sent_at = fixed_now or datetime.now(UTC)
            row.last_error = None
            _drop_link(row)
        await db.commit()
    return attempted


def _drop_link(row: EmailOutbox) -> None:
    """The link in an invite or reset mail is a live credential (R3): keep it only while the
    mail can still be sent, so neither a delivered nor a dead-lettered row holds it."""
    if row.template in LINK_TEMPLATES:
        row.body = "[link removed]"
        row.payload = {"recipient_name": row.payload.get("recipient_name", "")}


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
    if row.template in LINK_TEMPLATES:
        # The link was removed when the mail failed; a new invite or reset issues a fresh one.
        raise ProblemError(409, "Send a new invite or reset instead of retrying this email")
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
