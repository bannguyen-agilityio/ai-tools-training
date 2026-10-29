"""Sign-in throttling (R2). Counts failed attempts per email and attempts per IP.

Refused attempts are not recorded, so an attacker cannot keep a victim locked out by retrying.
"""

import hashlib
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import LoginAttempt

WINDOW = timedelta(minutes=15)
EMAIL_FAILURES = 5


def email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


async def is_blocked(
    db: AsyncSession, *, email: str, ip: str, ip_limit: int, now: datetime
) -> bool:
    since = now - WINDOW
    failures = await db.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(
            LoginAttempt.email_hash == email_hash(email),
            LoginAttempt.success.is_(False),
            LoginAttempt.at > since,
        )
    )
    if (failures or 0) >= EMAIL_FAILURES:
        return True
    from_ip = await db.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(LoginAttempt.ip == ip, LoginAttempt.success.is_(False), LoginAttempt.at > since)
    )
    return (from_ip or 0) >= ip_limit


async def record(db: AsyncSession, *, email: str, ip: str, success: bool, now: datetime) -> None:
    db.add(LoginAttempt(email_hash=email_hash(email), ip=ip, at=now, success=success))
    await db.flush()
