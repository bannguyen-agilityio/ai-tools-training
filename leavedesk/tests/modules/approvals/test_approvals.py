import asyncio
import uuid
from datetime import date

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.balances.me_router import get_today
from tests.conftest import Login, MakeLogin
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.requests.conftest import set_manager
from tests.modules.requests.test_requests import body, post

TODAY = date(2026, 6, 1)
LIST = "/api/v1/approvals"


@pytest.fixture(autouse=True)
def fixed_today(app: FastAPI) -> None:
    app.dependency_overrides[get_today] = lambda: TODAY


@pytest.fixture
async def staff(make_login: MakeLogin, owner_engine: AsyncEngine) -> tuple[Login, Login]:
    emp, mgr = await make_login(), await make_login("manager")
    await set_manager(owner_engine, emp, mgr)
    await seed_year(owner_engine, emp.employee_id, "entitlement", "12")
    return emp, mgr


async def submit(client: httpx.AsyncClient, emp: Login, **kw: object) -> str:
    r = await post(client, emp, body(**kw))  # type: ignore[arg-type]
    assert r.status_code == 201, r.text
    return str(r.json()["id"])


def act(rid: object, what: str) -> str:
    return f"/api/v1/approvals/{rid}/{what}"


async def decide(
    client: httpx.AsyncClient, who: Login, rid: object, what: str = "approve", **payload: object
) -> httpx.Response:
    payload.setdefault("version", 1)
    return await client.post(act(rid, what), json=payload, headers=who.mutating_headers)


async def scalar(owner: AsyncEngine, sql: str, **params: object) -> object:
    async with owner.connect() as conn:
        return await conn.scalar(text(sql), params)


async def status_of(client: httpx.AsyncClient, who: Login, rid: object) -> str:
    r = await client.get(f"/api/v1/requests/{rid}", headers=who.headers)
    return str(r.json()["status"])


# --- AuthZ -----------------------------------------------------------------------------------


async def test_requires_session_and_csrf(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    assert (await client.get(LIST)).status_code == 401
    assert (await client.post(act(rid, "approve"), json={"version": 1})).status_code == 401
    reject = await client.post(act(rid, "reject"), json={"version": 1, "reason": "x"})
    assert reject.status_code == 401
    no_csrf = await client.post(act(rid, "approve"), json={"version": 1}, headers=mgr.headers)
    assert no_csrf.status_code == 403


async def test_role_matrix(client: httpx.AsyncClient, staff, make_login: MakeLogin) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    other_mgr, hr, peer = await make_login("manager"), await make_login("hr"), await make_login()
    for who in (emp, other_mgr, hr, peer):
        for what, extra in (("approve", {}), ("reject", {"reason": "no"})):
            r = await decide(client, who, rid, what, **extra)
            assert r.status_code == 403, (who, what)
    assert await status_of(client, mgr, rid) == "pending"


async def test_denied_attempt_is_logged_without_detail(
    client: httpx.AsyncClient, staff, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    rid = await submit(client, emp)
    other = await make_login("manager")
    assert (await decide(client, other, rid)).status_code == 403
    assert (await decide(client, other, rid, "reject", reason="secret words")).status_code == 403
    async with owner_engine.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT action, actor_id, detail::text FROM audit_log"
                    " WHERE action LIKE '%_denied'"
                )
            )
        ).all()
    assert sorted(r[0] for r in rows) == ["approve_denied", "reject_denied"]
    assert all(r[1] == other.employee_id and "secret" not in r[2] for r in rows)


async def test_self_approval_refused_for_every_role(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    mgr, hr = await make_login("manager"), await make_login("hr")
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    rid = await submit(client, mgr)  # manager -> HR queue
    assert (await decide(client, mgr, rid)).status_code == 403
    assert (await decide(client, hr, rid)).status_code == 200


async def test_unknown_request_404(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    assert (await decide(client, staff[1], uuid.uuid4())).status_code == 404


# --- R18 -------------------------------------------------------------------------------------


async def test_approve(client: httpx.AsyncClient, staff, owner_engine: AsyncEngine) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp, note="trip")
    r = await decide(client, mgr, rid)
    assert r.status_code == 200
    assert (r.json()["status"], r.json()["version"]) == ("approved", 2)
    assert (
        await scalar(owner_engine, "SELECT decided_by FROM leave_request WHERE id = :i", i=rid)
        == mgr.employee_id
    )
    active = "SELECT count(*) FROM leave_request_day WHERE request_id = :i AND is_active"
    assert await scalar(owner_engine, active, i=rid) == 2
    mail = (
        "SELECT count(*) FROM email_outbox WHERE template = 'request_approved'"
        " AND recipient_employee_id = :e"
    )
    assert await scalar(owner_engine, mail, e=emp.employee_id) == 1
    audit = "SELECT count(*) FROM audit_log WHERE action = 'request.approve'"
    assert await scalar(owner_engine, audit) == 1


async def test_stale_version_and_repeat_conflict(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    stale = await decide(client, mgr, rid, version=7)
    assert stale.status_code == 409
    assert stale.json()["error"]["message"] == "This request was already decided."
    assert (await decide(client, mgr, rid)).status_code == 200
    again = await decide(client, mgr, rid)
    assert again.status_code == 409
    assert again.json()["error"]["message"] == "This request was already decided."


async def test_two_simultaneous_decisions_one_wins(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    first, second = await asyncio.gather(
        decide(client, mgr, rid), decide(client, mgr, rid, "reject", reason="no")
    )
    assert sorted([first.status_code, second.status_code]) == [200, 409]
    audit = "SELECT count(*) FROM audit_log WHERE action IN ('request.approve','request.reject')"
    assert await scalar(owner_engine, audit) == 1


# --- R19 -------------------------------------------------------------------------------------


@pytest.mark.parametrize("reason", ["", "   ", "\t\n", "x" * 501])
async def test_reject_reason_validation(client: httpx.AsyncClient, staff, reason: str) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    r = await decide(client, mgr, rid, "reject", reason=reason)
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"].endswith("reason")
    assert await status_of(client, emp, rid) == "pending"


async def test_reject_500_ok_and_releases_days(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    r = await decide(client, mgr, rid, "reject", reason=f"  {'r' * 500}  ")
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    active = "SELECT count(*) FROM leave_request_day WHERE request_id = :i AND is_active"
    assert await scalar(owner_engine, active, i=rid) == 0
    assert (await post(client, emp, body())).status_code == 201  # the dates are free again


async def test_rejection_reason_reaches_only_the_employee(
    client: httpx.AsyncClient, staff, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    rid = await submit(client, emp)
    assert (await decide(client, mgr, rid, "reject", reason="budget zebra")).status_code == 200
    async with owner_engine.connect() as conn:
        mails = (
            await conn.execute(
                text(
                    "SELECT recipient_employee_id, body FROM email_outbox"
                    " WHERE template = 'request_rejected'"
                )
            )
        ).all()
        assert [m[0] for m in mails] == [emp.employee_id]
        assert "budget zebra" in mails[0][1]
        leaks = await conn.scalar(
            text("SELECT count(*) FROM audit_log WHERE detail::text LIKE '%zebra%'")
        )
        assert leaks == 0


# --- List and privacy ------------------------------------------------------------------------


async def test_list_assigned_scoped_and_redacted(
    client: httpx.AsyncClient, staff, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    rid = await submit(client, emp, leave_type="sick", note="flu")
    other = await make_login("manager")
    assert (await client.get(LIST, headers=other.headers)).json()["items"] == []
    assert (await client.get(LIST, headers=emp.headers)).status_code == 403
    items = (await client.get(LIST, headers=mgr.headers)).json()["items"]
    assert [i["id"] for i in items] == [rid]
    assert items[0]["leave_type"] == "sick" and items[0]["note"] == "flu"  # while deciding
    assert (await client.get(f"{LIST}?scope=bogus", headers=mgr.headers)).status_code == 422
    done = await decide(client, mgr, rid)
    assert done.json()["leave_type"] is None and done.json()["note"] is None
    assert (await client.get(LIST, headers=mgr.headers)).json()["items"] == []
    mail = await scalar(
        owner_engine, "SELECT body FROM email_outbox WHERE template = 'request_approved'"
    )
    assert "sick" not in str(mail).lower() and "flu" not in str(mail)


async def test_hr_queue_for_hr_not_other_managers(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:  # type: ignore[no-untyped-def]
    mgr, hr = await make_login("manager"), await make_login("hr")
    other = await make_login("manager")
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    rid = await submit(client, mgr)
    assert [i["id"] for i in (await client.get(LIST, headers=hr.headers)).json()["items"]] == [rid]
    assert (await client.get(LIST, headers=other.headers)).json()["items"] == []
    assert (await decide(client, other, rid)).status_code == 403
    assert (await decide(client, hr, rid, "reject", reason="no")).status_code == 200


# --- Plan open items -------------------------------------------------------------------------


async def test_plain_employee_list_is_403(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    assert (await client.get(LIST, headers=emp.headers)).status_code == 403


async def test_cards_carry_requester_name(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, mgr = staff
    await submit(client, emp)
    items = (await client.get(LIST, headers=mgr.headers)).json()["items"]
    assert [i["employee_name"] for i in items] == ["Test"]


async def test_hr_who_entered_a_request_cannot_decide_it(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, other_hr, mgr = await make_login("hr"), await make_login("hr"), await make_login("manager")
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    made = await client.post(
        "/api/v1/hr/requests",
        json={**body("2026-06-08"), "employee_id": str(mgr.employee_id), "entry_reason": "phone"},
        headers=hr.mutating_headers,
    )
    assert made.status_code == 201, made.text
    rid = made.json()["id"]
    assert (await decide(client, hr, rid)).status_code == 403
    assert rid not in [
        i["id"] for i in (await client.get(LIST, headers=hr.headers)).json()["items"]
    ]
    assert (await decide(client, other_hr, rid)).status_code == 200
