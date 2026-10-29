"""Sign-in, invite, reset and password change (R1, R2, R3).

Audit rows carry the email hash only, never the address, password or a token (spec §8).
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.csrf import hash_token, new_token
from app.core.errors import ProblemError
from app.modules.audit import service as audit
from app.modules.auth import ratelimit, repository, tokens
from app.modules.auth.models import UserIdentity
from app.modules.auth.passwords import (
    DUMMY_HASH,
    PasswordPolicyError,
    hash_password,
    needs_rehash,
    validate_password,
    verify_password,
)
from app.modules.auth.schemas import MeOut, TeamOut
from app.modules.email.templates import Event
from app.modules.identity.models import Employee, Session, Team
from app.modules.notifications import service as notifications

COMPANY_DOMAIN = "@asnet.com.vn"
GENERIC_LOGIN_ERROR = "Email or password is incorrect"
BAD_LINK = "This link has expired or was already used. Request a new one."


class InvalidEmailDomain(ValueError):
    pass


def require_company_email(email: str) -> None:
    """R1: only company addresses get accounts. The DB CHECK is the backstop."""
    if not email.strip().lower().endswith(COMPANY_DOMAIN):
        raise InvalidEmailDomain(f"Email must end with {COMPANY_DOMAIN}")


def _now() -> datetime:
    return datetime.now(UTC)


def _check_password(password: str) -> None:
    try:
        validate_password(password)
    except PasswordPolicyError as exc:
        raise ProblemError(422, str(exc)) from exc


async def profile(db: AsyncSession, employee: Employee, csrf: str) -> MeOut:
    team = await db.get(Team, employee.team_id) if employee.team_id else None
    return MeOut(
        id=employee.id,
        name=employee.name,
        email=employee.email,
        role=employee.role,
        is_hr_deputy=employee.is_hr_deputy,
        team=TeamOut(id=team.id, name=team.name) if team else None,
        csrf_token=csrf,
    )


async def login(
    db: AsyncSession, *, email: str, password: str, ip: str, current_token: str | None
) -> tuple[str, Employee]:
    """Returns (new session token, employee). Raises 429 when throttled, generic 401 on failure."""
    settings = get_settings()
    now = _now()
    ehash = ratelimit.email_hash(email)

    if await ratelimit.is_blocked(
        db, email=email, ip=ip, ip_limit=settings.login_ip_limit, now=now
    ):
        await audit.record(
            db,
            actor_id=None,
            action="auth.login_locked",
            target_type="login",
            target_id=ehash[:16],
            ip=ip,
        )
        await db.commit()
        raise ProblemError(429, "Too many sign-in attempts. Try again in 15 minutes.")

    employee = await repository.employee_by_email(db, email)
    identity = await repository.password_identity(db, employee.id) if employee else None
    stored = identity.password_hash if identity and employee and employee.is_active else None
    # Always one Argon2 verification, so unknown/inactive/uninvited emails take the same time.
    verified = verify_password(stored or DUMMY_HASH, password)
    if not (verified and stored and employee and identity):
        await ratelimit.record(db, email=email, ip=ip, success=False, now=now)
        await audit.record(
            db,
            actor_id=None,
            action="auth.login_failed",
            target_type="login",
            target_id=ehash[:16],
            ip=ip,
        )
        await db.commit()
        raise ProblemError(401, GENERIC_LOGIN_ERROR)

    if needs_rehash(stored):
        identity.password_hash = hash_password(password)
    identity.last_login_at = now
    await ratelimit.record(db, email=email, ip=ip, success=True, now=now)

    # New token on every sign-in; a session presented with the request is ended (no fixation).
    if current_token:
        await repository.delete_session_by_hash(db, hash_token(current_token))
    raw = new_token()
    db.add(
        Session(
            employee_id=employee.id,
            token_hash=hash_token(raw),
            csrf_token_hash=hash_token(tokens.session_csrf(raw)),
            created_at=now,
            last_seen_at=now,
            expires_at=now
            + min(
                timedelta(hours=settings.session_idle_hours),
                timedelta(hours=settings.session_max_hours),
            ),
        )
    )
    await audit.record(
        db,
        actor_id=employee.id,
        action="auth.login",
        target_type="employee",
        target_id=str(employee.id),
        ip=ip,
    )
    await db.commit()
    return raw, employee


async def logout(db: AsyncSession, employee: Employee, token: str) -> None:
    await repository.delete_session_by_hash(db, hash_token(token))
    await audit.record(
        db,
        actor_id=employee.id,
        action="auth.logout",
        target_type="employee",
        target_id=str(employee.id),
    )
    await db.commit()


async def _ensure_identity(db: AsyncSession, employee_id: uuid.UUID) -> UserIdentity:
    identity = await repository.password_identity(db, employee_id)
    if identity is None:
        identity = UserIdentity(employee_id=employee_id, provider="password")
        db.add(identity)
        await db.flush()
    return identity


async def issue_invite(db: AsyncSession, employee: Employee, now: datetime | None = None) -> str:
    """Called by HR employee create/re-send (plan 07); the caller commits.

    Voids any earlier invite, queues the email and returns the raw token for tests only: HR
    endpoints must never put it in a response (R3).
    """
    require_company_email(employee.email)
    now = now or _now()
    await _ensure_identity(db, employee.id)
    raw, row = await tokens.issue(db, employee.id, "invite", now)
    link = f"{get_settings().app_base_url}/set-password?token={raw}"
    await notifications.emit(db, Event.INVITE, employee, link=link, occurrence=str(row.id))
    await audit.record(
        db,
        actor_id=None,
        action="auth.invite_issued",
        target_type="employee",
        target_id=str(employee.id),
    )
    return raw


async def issue_reset(db: AsyncSession, employee: Employee, now: datetime | None = None) -> str:
    now = now or _now()
    raw, row = await tokens.issue(db, employee.id, "reset", now)
    link = f"{get_settings().app_base_url}/reset-password?token={raw}"
    await notifications.emit(db, Event.PASSWORD_RESET, employee, link=link, occurrence=str(row.id))
    await audit.record(
        db,
        actor_id=None,
        action="auth.reset_requested",
        target_type="employee",
        target_id=str(employee.id),
    )
    return raw


async def request_reset(db: AsyncSession, email: str) -> None:
    """Looks the same to the caller; only active accounts with a password identity get mail."""
    employee = await repository.employee_by_email(db, email)
    if employee and employee.is_active and await repository.password_identity(db, employee.id):
        await issue_reset(db, employee)
    await db.commit()


async def _set_password_with_token(
    db: AsyncSession, *, raw_token: str, purpose: str, password: str, action: str
) -> None:
    now = _now()
    # Check the token first so a weak password does not burn it, then consume atomically.
    if await tokens.peek(db, raw_token, purpose, now) is None:
        raise ProblemError(400, BAD_LINK)
    _check_password(password)
    employee_id = await tokens.consume(db, raw_token, purpose, now)
    if employee_id is None:
        raise ProblemError(400, BAD_LINK)
    employee = await db.get(Employee, employee_id)
    if employee is None or not employee.is_active:
        raise ProblemError(400, BAD_LINK)
    identity = await _ensure_identity(db, employee_id)
    identity.password_hash = hash_password(password)
    identity.password_changed_at = now
    await repository.delete_sessions(db, employee_id)
    await audit.record(
        db, actor_id=employee_id, action=action, target_type="employee", target_id=str(employee_id)
    )
    await db.commit()


async def accept_invite(db: AsyncSession, token: str, password: str) -> None:
    await _set_password_with_token(
        db, raw_token=token, purpose="invite", password=password, action="auth.invite_accepted"
    )


async def confirm_reset(db: AsyncSession, token: str, password: str) -> None:
    await _set_password_with_token(
        db, raw_token=token, purpose="reset", password=password, action="auth.reset_confirmed"
    )


async def change_password(
    db: AsyncSession,
    employee: Employee,
    *,
    current: str,
    new: str,
    session_token: str,
    ip: str,
) -> None:
    """Wrong current passwords count toward the sign-in lockout, so a stolen session can't guess."""
    settings = get_settings()
    now = _now()
    if await ratelimit.is_blocked(
        db, email=employee.email, ip=ip, ip_limit=settings.login_ip_limit, now=now
    ):
        raise ProblemError(429, "Too many attempts. Try again in 15 minutes.")
    identity = await repository.password_identity(db, employee.id)
    if not (
        identity and identity.password_hash and verify_password(identity.password_hash, current)
    ):
        await ratelimit.record(db, email=employee.email, ip=ip, success=False, now=now)
        await db.commit()
        raise ProblemError(403, "Current password is incorrect")
    _check_password(new)
    identity.password_hash = hash_password(new)
    identity.password_changed_at = now
    await repository.delete_sessions(db, employee.id, keep_token_hash=hash_token(session_token))
    await audit.record(
        db,
        actor_id=employee.id,
        action="auth.password_changed",
        target_type="employee",
        target_id=str(employee.id),
        ip=ip,
    )
    await db.commit()
