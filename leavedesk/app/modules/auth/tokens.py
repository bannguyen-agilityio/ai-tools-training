"""One-time invite and reset tokens (R3). Only the sha256 of a token is stored."""

import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from hashlib import sha256

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.csrf import hash_token
from app.modules.auth.models import OneTimeToken

TTL = {"invite": timedelta(hours=48), "reset": timedelta(hours=1)}


async def issue(
    db: AsyncSession, employee_id: uuid.UUID, purpose: str, now: datetime
) -> tuple[str, OneTimeToken]:
    """Create a token and void any earlier unused one for the same purpose."""
    await db.execute(
        update(OneTimeToken)
        .where(
            OneTimeToken.employee_id == employee_id,
            OneTimeToken.purpose == purpose,
            OneTimeToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    raw = secrets.token_urlsafe(32)
    row = OneTimeToken(
        employee_id=employee_id,
        purpose=purpose,
        token_hash=hash_token(raw),
        expires_at=now + TTL[purpose],
    )
    db.add(row)
    await db.flush()
    return raw, row


async def peek(db: AsyncSession, raw: str, purpose: str, now: datetime) -> OneTimeToken | None:
    """The token row if it is valid right now (no change made)."""
    return await db.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == hash_token(raw),
            OneTimeToken.purpose == purpose,
            OneTimeToken.used_at.is_(None),
            OneTimeToken.expires_at > now,
        )
    )


async def consume(db: AsyncSession, raw: str, purpose: str, now: datetime) -> uuid.UUID | None:
    """Atomically mark the token used. Returns the employee id, or None if unusable.

    The conditional UPDATE means two concurrent requests cannot both succeed (single use).
    """
    return await db.scalar(
        update(OneTimeToken)
        .where(
            OneTimeToken.token_hash == hash_token(raw),
            OneTimeToken.purpose == purpose,
            OneTimeToken.used_at.is_(None),
            OneTimeToken.expires_at > now,
        )
        .values(used_at=now)
        .returning(OneTimeToken.employee_id)
    )


def session_csrf(session_token: str) -> str:
    """CSRF token derived from the session token, so GET /me can return it without storing it.

    Stdlib HMAC-SHA256 keyed by the (secret) session token; only its hash is stored.
    """
    return hmac.new(session_token.encode(), b"csrf", sha256).hexdigest()
