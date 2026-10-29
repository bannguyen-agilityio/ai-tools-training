from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.config import get_settings
from app.core.csrf import CSRF_HEADER, SAFE_METHODS, hash_token, tokens_match
from app.core.db import get_db
from app.core.errors import ProblemError
from app.modules.identity.models import Employee, Session

SESSION_COOKIE = "session"


def get_current_user(request: Request, db: Annotated[DbSession, Depends(get_db)]) -> Employee:
    """Authenticate from the hashed session cookie (R29a, R2) and enforce CSRF (R29c)."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise ProblemError(401, "Authentication required")

    session = db.scalar(select(Session).where(Session.token_hash == hash_token(token)))
    now = datetime.now(UTC)
    if session is None or session.expires_at <= now:
        raise ProblemError(401, "Authentication required")

    employee = db.get(Employee, session.employee_id)
    if employee is None or not employee.is_active:
        raise ProblemError(401, "Authentication required")

    if request.method not in SAFE_METHODS and not tokens_match(
        request.headers.get(CSRF_HEADER), session.csrf_token_hash
    ):
        raise ProblemError(403, "Missing or invalid CSRF token")

    # Sliding idle window, capped by the absolute maximum.
    settings = get_settings()
    session.last_seen_at = now
    session.expires_at = min(
        now + timedelta(hours=settings.session_idle_hours),
        session.created_at + timedelta(hours=settings.session_max_hours),
    )
    db.commit()
    request.state.employee_id = employee.id
    return employee


CurrentUser = Annotated[Employee, Depends(get_current_user)]


def require_hr(user: CurrentUser) -> Employee:
    if user.role != "hr":
        raise ProblemError(403, "Not allowed")
    return user
