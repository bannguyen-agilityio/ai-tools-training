import uuid

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import MakeLogin
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.requests.test_requests import body, outbox, post

BALANCES = "/api/v1/me/balances"


def url(rid: str) -> str:
    return f"/api/v1/requests/{rid}/cancel"


async def make(client: httpx.AsyncClient, emp) -> dict:  # type: ignore[no-untyped-def,type-arg]
    r = await post(client, emp, body("2026-06-08", "2026-06-10"))
    assert r.status_code == 201
    return r.json()  # type: ignore[no-any-return]


async def reserved(client: httpx.AsyncClient, emp) -> float:  # type: ignore[no-untyped-def]
    r = await client.get(BALANCES, headers=emp.headers)
    annual = next(b for b in r.json()["balances"] if b["leave_type"] == "annual")
    return float(annual["reserved"])


async def test_requires_session_and_csrf(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    req = await make(client, emp)
    assert (await client.post(url(req["id"]), json={"version": 1})).status_code == 401
    r = await client.post(url(req["id"]), json={"version": 1}, headers=emp.headers)
    assert r.status_code == 403  # no CSRF token


async def test_owner_cancels_pending_and_releases_days(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    req = await make(client, emp)
    assert await reserved(client, emp) == 3.0
    r = await post(client, emp, {"version": req["version"]}, url(req["id"]))
    assert r.status_code == 200
    j = r.json()
    assert (j["status"], j["version"]) == ("cancelled", 2)
    assert await reserved(client, emp) == 0.0
    async with owner_engine.connect() as conn:
        active = await conn.scalar(
            text("SELECT count(*) FROM leave_request_day WHERE request_id = :r AND is_active"),
            {"r": uuid.UUID(req["id"])},
        )
        row = (
            await conn.execute(
                text("SELECT cancelled_by, cancelled_at FROM leave_request WHERE id = :r"),
                {"r": uuid.UUID(req["id"])},
            )
        ).one()
        audit = (
            await conn.execute(
                text("SELECT detail::text FROM audit_log WHERE action = 'request.cancel'")
            )
        ).all()
    assert active == 0
    assert row.cancelled_by == emp.employee_id and row.cancelled_at is not None
    assert len(audit) == 1 and "private" not in audit[0][0]
    assert await outbox(owner_engine, "request_cancelled_by_employee") == [str(mgr.employee_id)]
    async with owner_engine.connect() as conn:
        n = await conn.scalar(
            text("SELECT count(*) FROM notification WHERE employee_id = :m"),
            {"m": mgr.employee_id},
        )
    assert n == 2  # created + cancelled


async def test_cancelled_dates_can_be_booked_again(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    req = await make(client, emp)
    await post(client, emp, {"version": 1}, url(req["id"]))
    assert (await post(client, emp, body("2026-06-08", "2026-06-10"))).status_code == 201


async def test_not_owner_is_403(client: httpx.AsyncClient, staff, make_login: MakeLogin) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    req = await make(client, emp)
    for who in (mgr, await make_login(), await make_login("hr")):
        r = await post(client, who, {"version": 1}, url(req["id"]))
        assert r.status_code == 403
    assert await reserved(client, emp) == 3.0


async def test_non_pending_is_403(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    for status in ("approved", "rejected"):
        req = await post(client, emp, body("2026-07-06" if status == "approved" else "2026-07-13"))
        rid = req.json()["id"]
        async with owner_engine.connect() as conn:
            await conn.execute(
                text("UPDATE leave_request SET status = :s, decision_reason = :d WHERE id = :r"),
                {"s": status, "d": "no" if status == "rejected" else None, "r": uuid.UUID(rid)},
            )
        r = await post(client, emp, {"version": 1}, url(rid))
        assert r.status_code == 403, status
        async with owner_engine.connect() as conn:
            assert (
                await conn.scalar(
                    text("SELECT status FROM leave_request WHERE id = :r"), {"r": uuid.UUID(rid)}
                )
                == status
            )


async def test_double_cancel_releases_once(client: httpx.AsyncClient, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    req = await make(client, emp)
    assert (await post(client, emp, {"version": 1}, url(req["id"]))).status_code == 200
    again = await post(client, emp, {"version": 2}, url(req["id"]))
    assert again.status_code == 403
    assert await reserved(client, emp) == 0.0
    assert await outbox(owner_engine, "request_cancelled_by_employee") == [str(mgr.employee_id)]


async def test_stale_version_is_409(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    req = await make(client, emp)
    r = await post(client, emp, {"version": 7}, url(req["id"]))
    assert r.status_code == 409
    assert await reserved(client, emp) == 3.0


async def test_unknown_request_and_bad_body(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    assert (await post(client, emp, {"version": 1}, url(str(uuid.uuid4())))).status_code == 404
    req = await make(client, emp)
    assert (await post(client, emp, {"version": 1, "x": 1}, url(req["id"]))).status_code == 400
    assert (await post(client, emp, {}, url(req["id"]))).status_code == 422


async def test_manager_request_notifies_hr_approvers(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    mgr, hr = await make_login("manager"), await make_login("hr")
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    r = await post(client, mgr, body("2026-06-08"))
    assert r.status_code == 201
    c = await post(client, mgr, {"version": 1}, url(r.json()["id"]))
    assert c.status_code == 200
    assert await outbox(owner_engine, "request_cancelled_by_employee") == [str(hr.employee_id)]
