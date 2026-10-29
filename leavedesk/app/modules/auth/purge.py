from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import LoginAttempt, OneTimeToken
from app.modules.identity.models import Session

ATTEMPT_RETENTION = timedelta(days=30)


async def purge(db: AsyncSession, now: datetime) -> dict[str, int]:
    """Delete expired sessions, used or expired tokens and attempts older than 30 days (§5.6)."""
    sessions = await db.execute(delete(Session).where(Session.expires_at <= now))
    tokens = await db.execute(
        delete(OneTimeToken).where(
            or_(OneTimeToken.used_at.is_not(None), OneTimeToken.expires_at <= now)
        )
    )
    attempts = await db.execute(
        delete(LoginAttempt).where(LoginAttempt.at <= now - ATTEMPT_RETENTION)
    )
    await db.commit()
    return {
        name: cast(CursorResult[Any], result).rowcount
        for name, result in (("sessions", sessions), ("tokens", tokens), ("attempts", attempts))
    }
