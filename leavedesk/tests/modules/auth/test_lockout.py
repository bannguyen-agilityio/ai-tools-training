from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.auth.ratelimit import email_hash
from tests.modules.auth.conftest import PASSWORD, MakeUser

URL = "/api/v1/auth/login"


async def _fail(owner: AsyncEngine, email: str, n: int, ago: timedelta, ip: str = "10.0.0.1"):
    async with owner.connect() as c:
        for _ in range(n):
            await c.execute(
                text(
                    "INSERT INTO login_attempt (email_hash, ip, at, success) "
                    "VALUES (:h,:ip,:at,false)"
                ),
                {"h": email_hash(email), "ip": ip, "at": datetime.now(UTC) - ago},
            )


async def test_sixth_attempt_refused_even_with_correct_password(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    for _ in range(5):
        r = await client.post(URL, json={"email": u.email, "password": "bad-bad-bad-12"})
        assert r.status_code == 401
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 429
    async with owner_engine.connect() as c:
        n = await c.scalar(text("SELECT count(*) FROM audit_log WHERE action='auth.login_locked'"))
    assert n == 1


async def test_lock_ends_after_15_minutes(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    await _fail(owner_engine, u.email, 5, timedelta(minutes=16))
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 200


async def test_lock_applies_to_unknown_email_too(
    client: httpx.AsyncClient, owner_engine: AsyncEngine
):
    await _fail(owner_engine, "ghost@asnet.com.vn", 5, timedelta(minutes=1))
    r = await client.post(URL, json={"email": "ghost@asnet.com.vn", "password": "x" * 14})
    assert r.status_code == 429


async def test_refused_attempts_do_not_extend_lock(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    await _fail(owner_engine, u.email, 5, timedelta(minutes=1))
    await client.post(URL, json={"email": u.email, "password": PASSWORD})
    async with owner_engine.connect() as c:
        n = await c.scalar(
            text("SELECT count(*) FROM login_attempt WHERE email_hash=:h"),
            {"h": email_hash(u.email)},
        )
    assert n == 5


async def test_per_ip_limit(
    client: httpx.AsyncClient, owner_engine: AsyncEngine, make_user: MakeUser
):
    u = await make_user()
    await _fail(owner_engine, "other@asnet.com.vn", 30, timedelta(minutes=1), ip="127.0.0.1")
    r = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert r.status_code == 429


async def test_audit_has_no_email_or_password(
    client: httpx.AsyncClient, make_user: MakeUser, owner_engine: AsyncEngine
):
    u = await make_user()
    await client.post(URL, json={"email": u.email, "password": "bad-bad-bad-12"})
    async with owner_engine.connect() as c:
        rows = (
            await c.execute(
                text(
                    "SELECT target_id, detail::text FROM audit_log WHERE action='auth.login_failed'"
                )
            )
        ).all()
    assert len(rows) == 1
    blob = " ".join(str(x) for x in rows[0])
    assert u.email not in blob and "bad-bad" not in blob
