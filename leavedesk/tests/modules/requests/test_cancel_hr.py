import asyncio
import uuid

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin
from tests.modules.requests.test_cancel_own import make, reserved
from tests.modules.requests.test_requests import outbox, post

REASON = "Office closed for the audit"


def url(rid: str) -> str:
    return f"/api/v1/requests/{rid}/cancel"


async def approve(owner: AsyncEngine, rid: str) -> None:
    async with owner.connect() as conn:
        await conn.execute(
            text("UPDATE leave_request SET status = 'approved' WHERE id = :r"),
            {"r": uuid.UUID(rid)},
        )


async def used(client: httpx.AsyncClient, emp: Login) -> float:
    r = await client.get("/api/v1/me/balances", headers=emp.headers)
    annual = next(b for b in r.json()["balances"] if b["leave_type"] == "annual")
    return float(annual["used"])


async def test_requires_session_and_csrf(client: httpx.AsyncClient, staff, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    body = {"version": 1, "reason": REASON}
    assert (await client.post(url(req["id"]), json=body)).status_code == 401


async def test_hr_cancels_approved_refunds_and_notifies(
    client: httpx.AsyncClient, staff, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    hr = await make_login("hr")
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    assert await used(client, emp) == 3.0
    r = await post(client, hr, {"version": 1, "reason": REASON}, url(req["id"]))
    assert r.status_code == 200, r.text
    assert (r.json()["status"], r.json()["version"]) == ("cancelled", 2)
    assert await used(client, emp) == 0.0
    assert await reserved(client, emp) == 0.0
    async with owner_engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT cancelled_by, cancel_reason FROM leave_request WHERE id = :r"),
                {"r": uuid.UUID(req["id"])},
            )
        ).one()
        audit = (
            await conn.execute(
                text("SELECT actor_id, detail::text FROM audit_log WHERE action = 'request.cancel'")
            )
        ).all()
        bodies = (
            await conn.execute(
                text("SELECT body, payload::text FROM email_outbox WHERE template = :t"),
                {"t": "request_cancelled_by_hr"},
            )
        ).all()
    assert row.cancelled_by == hr.employee_id and row.cancel_reason == REASON
    assert len(audit) == 1 and audit[0][0] == hr.employee_id
    assert REASON not in audit[0][1]
    assert sorted(await outbox(owner_engine, "request_cancelled_by_hr")) == sorted(
        [str(emp.employee_id), str(mgr.employee_id)]
    )
    for b in bodies:
        assert REASON not in b[0] and REASON not in b[1]
        assert "sick" not in b[0].lower()


async def test_reason_required(client: httpx.AsyncClient, staff, make_login, owner_engine) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr = await make_login("hr")
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    bad: list[dict[str, object]] = [
        {"version": 1},
        {"version": 1, "reason": "   "},
        {"version": 1, "reason": "x" * 501},
    ]
    for payload in bad:
        r = await post(client, hr, payload, url(req["id"]))
        assert r.status_code == 422, payload
    assert await used(client, emp) == 3.0


async def test_authz_matrix(
    client: httpx.AsyncClient, staff, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    deputy = await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"), {"d": deputy.employee_id}
        )
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    for who in (emp, mgr, deputy, await make_login()):
        r = await post(client, who, {"version": 1, "reason": REASON}, url(req["id"]))
        assert r.status_code == 403, who
    assert await used(client, emp) == 3.0


async def test_hr_cannot_cancel_pending(client: httpx.AsyncClient, staff, make_login) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr = await make_login("hr")
    req = await make(client, emp)
    r = await post(client, hr, {"version": 1, "reason": REASON}, url(req["id"]))
    assert r.status_code == 403


async def test_second_cancel_refunds_once(
    client: httpx.AsyncClient, staff, make_login, owner_engine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr = await make_login("hr")
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    body = {"version": 1, "reason": REASON}
    assert (await post(client, hr, body, url(req["id"]))).status_code == 200
    assert (await post(client, hr, body, url(req["id"]))).status_code == 403  # same version
    assert (await post(client, hr, {**body, "version": 2}, url(req["id"]))).status_code == 403
    assert await used(client, emp) == 0.0
    assert len(await outbox(owner_engine, "request_cancelled_by_hr")) == 2


async def test_concurrent_cancels_one_wins(
    client: httpx.AsyncClient, staff, make_login, owner_engine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr1, hr2 = await make_login("hr"), await make_login("hr")
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    body = {"version": 1, "reason": REASON}
    rs = await asyncio.gather(
        post(client, hr1, body, url(req["id"])), post(client, hr2, body, url(req["id"]))
    )
    assert sorted(r.status_code for r in rs)[0] == 200
    assert sorted(r.status_code for r in rs)[1] in (403, 409)
    assert await used(client, emp) == 0.0
    assert len(await outbox(owner_engine, "request_cancelled_by_hr")) == 2


async def test_stale_version_is_409(
    client: httpx.AsyncClient, staff, make_login, owner_engine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    hr = await make_login("hr")
    req = await make(client, emp)
    await approve(owner_engine, req["id"])
    r = await post(client, hr, {"version": 9, "reason": REASON}, url(req["id"]))
    assert r.status_code == 409
    assert await used(client, emp) == 3.0
