from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin


async def test_garbage_and_expired_sessions_are_401(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    r = await pclient.get("/api/v1/audit-log", headers={"Cookie": "session=nope"})
    assert r.status_code == 401
    expired = await make_login("hr", expires_in=timedelta(seconds=-1))
    assert (await pclient.get("/api/v1/audit-log", headers=expired.headers)).status_code == 401


async def test_deactivated_employee_session_is_401(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    gone = await make_login("hr", active=False)
    assert (await pclient.get("/api/v1/audit-log", headers=gone.headers)).status_code == 401


# R29c
async def test_post_without_csrf_token_is_403(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post("/api/v1/_probe", json={"name": "a"}, headers=u.headers)
    assert r.status_code == 403


async def test_post_with_wrong_csrf_token_is_403(
    pclient: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    u = await make_login()
    r = await pclient.post(
        "/api/v1/_probe", json={"name": "a"}, headers={**u.headers, "X-CSRF-Token": "x"}
    )
    assert r.status_code == 403


async def test_valid_csrf_passes(pclient: httpx.AsyncClient, make_login: MakeLogin) -> None:
    u = await make_login()
    r = await pclient.post("/api/v1/_probe", json={"name": "a"}, headers=u.mutating_headers)
    assert r.status_code == 200
    assert r.json() == {"name": "a"}


async def test_csrf_not_required_for_get(pclient: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    assert (await pclient.get("/api/v1/audit-log", headers=hr.headers)).status_code == 200


# R2 sliding window
async def test_session_expiry_slides_but_is_capped_at_24h(
    pclient: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    u = await make_login("hr", age=timedelta(hours=20), expires_in=timedelta(hours=1))
    assert (await pclient.get("/api/v1/audit-log", headers=u.headers)).status_code == 200
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT created_at, expires_at FROM session WHERE employee_id = :e"),
                {"e": u.employee_id},
            )
        ).one()
    created, expires = row
    assert expires == created + timedelta(hours=24)
    assert expires > datetime.now(UTC) + timedelta(hours=3)


async def test_sql_metacharacters_are_data_not_sql(
    pclient: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    u = await make_login("hr")
    evil = "x'; DROP TABLE employee;--"
    r = await pclient.get("/api/v1/audit-log", params={"limit": evil}, headers=u.headers)
    assert r.status_code == 422
    async with owner_engine.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM employee")) == 1
