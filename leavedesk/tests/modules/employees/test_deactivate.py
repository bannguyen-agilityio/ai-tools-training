import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin
from tests.modules.employees.test_employees import rows
from tests.modules.requests.test_requests import body, post

HR_URL = "/api/v1/hr/employees"


def url(eid: uuid.UUID) -> str:
    return f"{HR_URL}/{eid}/deactivate"


async def test_requires_session_and_csrf(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    emp, hr = await make_login(), await make_login("hr")
    assert (await client.post(url(emp.employee_id))).status_code == 401
    assert (await client.post(url(emp.employee_id), headers=hr.headers)).status_code == 403


async def test_only_hr_admin_may_deactivate(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    target, deputy = await make_login(), await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"),
            {"d": deputy.employee_id},
        )
    for who in (await make_login(), await make_login("manager"), deputy):
        r = await client.post(url(target.employee_id), headers=who.mutating_headers)
        assert r.status_code == 403
    assert (
        await rows(
            owner_engine, "SELECT is_active FROM employee WHERE id = :i", i=target.employee_id
        )
    )[0]["is_active"]


async def test_deactivation_ends_sessions_and_keeps_history(
    client: httpx.AsyncClient,
    staff: tuple[Login, Login],
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
) -> None:
    emp, mgr = staff
    hr = await make_login("hr")
    pend = (await post(client, emp, body("2026-06-08"))).json()
    done = (await post(client, emp, body("2026-07-06"))).json()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE leave_request SET status = 'approved' WHERE id = :r"),
            {"r": uuid.UUID(done["id"])},
        )
    r = await client.post(url(emp.employee_id), headers=hr.mutating_headers)
    assert r.status_code == 200 and r.json()["is_active"] is False

    # The stale cookie is refused and the sessions are gone.
    assert (await client.get("/api/v1/me/requests", headers=emp.headers)).status_code == 401
    assert (await post(client, emp, body("2026-08-03"))).status_code == 401
    assert (
        await rows(owner_engine, "SELECT 1 FROM session WHERE employee_id = :e", e=emp.employee_id)
    ) == []

    got = {
        x["id"]: x
        for x in await rows(
            owner_engine,
            "SELECT id::text AS id, status, cancelled_by FROM leave_request WHERE employee_id = :e",
            e=emp.employee_id,
        )
    }
    assert got[pend["id"]]["status"] == "cancelled"
    assert got[pend["id"]]["cancelled_by"] == hr.employee_id
    assert got[done["id"]]["status"] == "approved"  # history stays
    active = await rows(
        owner_engine,
        "SELECT count(*) AS n FROM leave_request_day WHERE request_id = :r AND is_active",
        r=uuid.UUID(pend["id"]),
    )
    assert active[0]["n"] == 0
    sent = await rows(
        owner_engine,
        "SELECT recipient_employee_id, body FROM email_outbox "
        "WHERE template = 'request_cancelled_on_deactivation'",
    )
    assert [s["recipient_employee_id"] for s in sent] == [mgr.employee_id]
    assert "sick" not in sent[0]["body"].lower()
    audits = await rows(
        owner_engine, "SELECT action FROM audit_log WHERE action IN ('employee.deactivate')"
    )
    assert len(audits) == 1


async def test_login_refused_after_deactivation(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    emp, hr = await make_login(), await make_login("hr")
    await client.post(url(emp.employee_id), headers=hr.mutating_headers)
    assert (await client.get("/api/v1/me", headers=emp.headers)).status_code == 401


async def test_unspecified_cases_refused(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, other_hr, deputy = await make_login("hr"), await make_login("hr"), await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :d"),
            {"d": deputy.employee_id},
        )
    for target in (hr, other_hr, deputy):
        r = await client.post(url(target.employee_id), headers=hr.mutating_headers)
        assert r.status_code == 422, target
    gone = await client.post(url(uuid.uuid4()), headers=hr.mutating_headers)
    assert gone.status_code == 404


async def test_second_deactivation_is_409(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    emp, hr = await make_login(), await make_login("hr")
    assert (await client.post(url(emp.employee_id), headers=hr.mutating_headers)).status_code == 200
    assert (await client.post(url(emp.employee_id), headers=hr.mutating_headers)).status_code == 409


async def test_failure_midway_rolls_everything_back(
    client: httpx.AsyncClient,
    staff: tuple[Login, Login],
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emp, _ = staff
    hr = await make_login("hr")
    pend = (await post(client, emp, body("2026-06-08"))).json()

    async def boom(*a: object, **k: object) -> None:
        raise RuntimeError("mail down")

    monkeypatch.setattr("app.modules.employees.deactivate.emit", boom)
    r = await client.post(url(emp.employee_id), headers=hr.mutating_headers)
    assert r.status_code == 500
    e = await rows(owner_engine, "SELECT is_active FROM employee WHERE id = :i", i=emp.employee_id)
    rq = await rows(
        owner_engine, "SELECT status FROM leave_request WHERE id = :i", i=uuid.UUID(pend["id"])
    )
    s = await rows(owner_engine, "SELECT 1 FROM session WHERE employee_id = :e", e=emp.employee_id)
    assert e[0]["is_active"] and rq[0]["status"] == "pending" and len(s) == 1
