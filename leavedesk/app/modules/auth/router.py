from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.modules.auth import service, tokens
from app.modules.auth.schemas import (
    LoginIn,
    MeOut,
    PasswordChangeIn,
    ResetRequestIn,
    TokenPasswordIn,
)
from app.modules.identity.dependencies import SESSION_COOKIE, CurrentUser

router = APIRouter(prefix="/api/v1", tags=["auth"])
DB = Annotated[AsyncSession, Depends(get_db)]


def client_ip(request: Request) -> str:
    """Peer address, or the right-most entry of the trusted proxy header when configured (A-6)."""
    header = get_settings().client_ip_header
    if header and (value := request.headers.get(header)):
        return value.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _session_token(request: Request) -> str:
    return request.cookies[SESSION_COOKIE]  # present: get_current_user already accepted it


@router.post("/auth/login", response_model=MeOut)
async def login(body: LoginIn, request: Request, response: Response, db: DB) -> MeOut:
    token, employee = await service.login(
        db,
        email=body.email,
        password=body.password,
        ip=client_ip(request),
        current_token=request.cookies.get(SESSION_COOKIE),
    )
    settings = get_settings()
    response.headers["Cache-Control"] = "no-store"  # the body carries the CSRF token
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_max_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return await service.profile(db, employee, tokens.session_csrf(token))


@router.post("/auth/logout", status_code=204)
async def logout(user: CurrentUser, request: Request, db: DB) -> Response:
    await service.logout(db, user, _session_token(request))
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.post("/auth/invite/accept", status_code=204)
async def accept_invite(body: TokenPasswordIn, db: DB) -> Response:
    await service.accept_invite(db, body.token, body.password)
    return Response(status_code=204)


@router.post("/auth/reset/request", status_code=202)
async def request_reset(body: ResetRequestIn, db: DB) -> dict[str, str]:
    await service.request_reset(db, body.email)
    return {"status": "accepted"}


@router.post("/auth/reset/confirm", status_code=204)
async def confirm_reset(body: TokenPasswordIn, db: DB) -> Response:
    await service.confirm_reset(db, body.token, body.password)
    return Response(status_code=204)


@router.post("/auth/password/change", status_code=204)
async def change_password(
    body: PasswordChangeIn, user: CurrentUser, request: Request, db: DB
) -> Response:
    await service.change_password(
        db,
        user,
        current=body.current_password,
        new=body.new_password,
        session_token=_session_token(request),
        ip=client_ip(request),
    )
    return Response(status_code=204)


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser, request: Request, response: Response, db: DB) -> MeOut:
    response.headers["Cache-Control"] = "no-store"
    return await service.profile(db, user, tokens.session_csrf(_session_token(request)))
