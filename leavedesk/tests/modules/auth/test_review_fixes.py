import asyncio

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.modules.auth import service
from app.modules.email.outbox_service import drain_due
from app.modules.identity.models import Employee
from tests.modules.auth.conftest import PASSWORD, MakeUser

URL = "/api/v1/auth/login"


async def test_concurrent_guesses_cannot_beat_the_lockout(
    client: httpx.AsyncClient, make_user: MakeUser
):
    u = await make_user()
    results = await asyncio.gather(
        *(
            client.post(URL, json={"email": u.email, "password": "bad-bad-bad-12"})
            for _ in range(20)
        )
    )
    codes = [r.status_code for r in results]
    assert codes.count(401) == 5 and codes.count(429) == 15


async def test_email_match_is_case_insensitive(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    r = await client.post(URL, json={"email": u.email.upper(), "password": PASSWORD})
    assert r.status_code == 200


async def test_auth_responses_are_not_cacheable(client: httpx.AsyncClient, make_user: MakeUser):
    u = await make_user()
    login = await client.post(URL, json={"email": u.email, "password": PASSWORD})
    assert login.headers["cache-control"] == "no-store"
    assert (await client.get("/api/v1/me")).headers["cache-control"] == "no-store"


class _Down:
    async def send(self, *, to: str, subject: str, body: str) -> None:
        raise RuntimeError("down")


async def test_link_removed_when_delivery_fails_for_good(
    make_user: MakeUser, app_engine: AsyncEngine, owner_engine: AsyncEngine
):
    u = await make_user(password=None)
    async with AsyncSession(app_engine, expire_on_commit=False) as s:
        e = await s.get(Employee, u.id)
        assert e
        token = await service.issue_invite(s, e)
        await s.commit()
    async with owner_engine.connect() as c:
        await c.execute(text("UPDATE email_outbox SET status='pending', attempts=4"))
    async with AsyncSession(app_engine) as s:
        await drain_due(s, _Down())
    async with owner_engine.connect() as c:
        row = (await c.execute(text("SELECT status, body, payload::text FROM email_outbox"))).one()
    assert row[0] == "failed" and token not in row[1] and token not in row[2]


async def test_hr_cannot_retry_a_failed_link_mail(
    client: httpx.AsyncClient, make_login, owner_engine: AsyncEngine
):
    hr = await make_login("hr")
    async with owner_engine.connect() as c:
        oid = await c.scalar(
            text(
                "INSERT INTO email_outbox (to_address, template, subject, body, dedupe_key, status)"
                " VALUES ('a@asnet.com.vn','invite','s','[link removed]','k1','failed')"
                " RETURNING id"
            )
        )
    r = await client.post(f"/api/v1/hr/email-outbox/{oid}/retry", headers=hr.mutating_headers)
    assert r.status_code == 409
