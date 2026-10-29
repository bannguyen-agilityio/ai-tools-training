import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.csrf import hash_token
from app.modules.auth import service
from app.modules.identity.models import Employee
from tests.modules.auth.conftest import PASSWORD, MakeUser

NEW_PW = "a brand new passphrase"
ACCEPT = "/api/v1/auth/invite/accept"
CONFIRM = "/api/v1/auth/reset/confirm"


async def _issue(app_engine: AsyncEngine, uid: uuid.UUID, purpose: str) -> str:
    async with AsyncSession(app_engine, expire_on_commit=False) as s:
        e = await s.get(Employee, uid)
        assert e
        token = (
            await service.issue_invite(s, e)
            if purpose == "invite"
            else await service.issue_reset(s, e)
        )
        await s.commit()
    return token


async def _age(owner: AsyncEngine, token: str, by: timedelta):
    async with owner.connect() as c:
        await c.execute(
            text("UPDATE one_time_token SET expires_at = expires_at - :d WHERE token_hash=:h"),
            {"d": by, "h": hash_token(token)},
        )


async def _bodies(owner: AsyncEngine) -> list[str]:
    async with owner.connect() as c:
        rows = await c.execute(text("SELECT body FROM email_outbox ORDER BY created_at"))
        return [r[0] for r in rows]


async def test_invite_flow_sets_first_password(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine
):
    u = await make_user(password=None)
    token = await _issue(app_engine, u.id, "invite")
    r = await client.post(ACCEPT, json={"token": token, "password": NEW_PW})
    assert r.status_code == 204
    login = await client.post("/api/v1/auth/login", json={"email": u.email, "password": NEW_PW})
    assert login.status_code == 200
    again = await client.post(ACCEPT, json={"token": token, "password": NEW_PW})
    assert again.status_code == 400


async def test_invite_expiry_48h(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine, owner_engine
):
    u = await make_user(password=None)
    token = await _issue(app_engine, u.id, "invite")
    await _age(owner_engine, token, timedelta(hours=49))
    r = await client.post(ACCEPT, json={"token": token, "password": NEW_PW})
    assert r.status_code == 400


async def test_new_invite_voids_previous(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine
):
    u = await make_user(password=None)
    old = await _issue(app_engine, u.id, "invite")
    new = await _issue(app_engine, u.id, "invite")
    assert (await client.post(ACCEPT, json={"token": old, "password": NEW_PW})).status_code == 400
    assert (await client.post(ACCEPT, json={"token": new, "password": NEW_PW})).status_code == 204


async def test_only_hash_stored_and_link_in_email(
    make_user: MakeUser, app_engine: AsyncEngine, owner_engine: AsyncEngine
):
    u = await make_user(password=None)
    token = await _issue(app_engine, u.id, "invite")
    async with owner_engine.connect() as c:
        stored = (await c.execute(text("SELECT token_hash FROM one_time_token"))).scalars().all()
    assert stored == [hash_token(token)]
    assert any(f"token={token}" in b for b in await _bodies(owner_engine))


async def test_purpose_is_enforced(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine
):
    u = await make_user()
    reset = await _issue(app_engine, u.id, "reset")
    r = await client.post(ACCEPT, json={"token": reset, "password": NEW_PW})
    assert r.status_code == 400


async def test_weak_password_keeps_token_usable(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine
):
    u = await make_user(password=None)
    token = await _issue(app_engine, u.id, "invite")
    weak = await client.post(ACCEPT, json={"token": token, "password": "password1234"})
    assert weak.status_code == 422
    assert (await client.post(ACCEPT, json={"token": token, "password": NEW_PW})).status_code == 204


async def test_reset_request_is_identical_for_known_and_unknown(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    a = await client.post("/api/v1/auth/reset/request", json={"email": u.email})
    b = await client.post("/api/v1/auth/reset/request", json={"email": "ghost@asnet.com.vn"})
    assert a.status_code == b.status_code == 202
    assert a.content == b.content
    assert len(await _bodies(owner_engine)) == 1


async def test_reset_not_sent_to_inactive(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user(active=False)
    await client.post("/api/v1/auth/reset/request", json={"email": u.email})
    assert await _bodies(owner_engine) == []


async def test_reset_confirm_kills_sessions_and_token_expires_at_1h(
    client: httpx.AsyncClient, make_user: MakeUser, app_engine: AsyncEngine, owner_engine
):
    u = await make_user()
    await client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    expired = await _issue(app_engine, u.id, "reset")
    await _age(owner_engine, expired, timedelta(minutes=61))
    r = await client.post(CONFIRM, json={"token": expired, "password": NEW_PW})
    assert r.status_code == 400
    token = await _issue(app_engine, u.id, "reset")
    assert (
        await client.post(CONFIRM, json={"token": token, "password": NEW_PW})
    ).status_code == 204
    assert (await client.get("/api/v1/me")).status_code == 401
    old = await client.post("/api/v1/auth/login", json={"email": u.email, "password": PASSWORD})
    assert old.status_code == 401
    new = await client.post("/api/v1/auth/login", json={"email": u.email, "password": NEW_PW})
    assert new.status_code == 200


async def test_reset_token_ttl_is_one_hour(
    make_user: MakeUser, app_engine: AsyncEngine, owner_engine: AsyncEngine
):
    u = await make_user()
    token = await _issue(app_engine, u.id, "reset")
    async with owner_engine.connect() as c:
        exp = await c.scalar(
            text("SELECT expires_at FROM one_time_token WHERE token_hash=:h"),
            {"h": hash_token(token)},
        )
    assert timedelta(minutes=59) < exp - datetime.now(UTC) <= timedelta(hours=1)
