import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.balances.me_router import get_today
from tests.conftest import Login, MakeLogin
from tests.modules.approvals.test_approvals import (
    LIST,
    TODAY,
    decide,
    scalar,
    status_of,
    submit,
)
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.requests.conftest import set_manager


@pytest.fixture(autouse=True)
def fixed_today(app: FastAPI) -> None:
    app.dependency_overrides[get_today] = lambda: TODAY


@pytest.fixture
async def staff(make_login: MakeLogin, owner_engine: AsyncEngine) -> tuple[Login, Login]:
    emp, mgr = await make_login(), await make_login("manager")
    await set_manager(owner_engine, emp, mgr)
    await seed_year(owner_engine, emp.employee_id, "entitlement", "12")
    return emp, mgr


async def cover_list(client: httpx.AsyncClient, who, scope: str = "cover") -> httpx.Response:  # type: ignore[no-untyped-def]
    return await client.get(f"{LIST}?scope={scope}", headers=who.headers)


async def test_cover_lists_other_managers_reports_only(
    client: httpx.AsyncClient,
    staff,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,  # type: ignore[no-untyped-def]
) -> None:
    emp, mgr = staff
    rid = await submit(client, emp)
    cover = await make_login("manager")
    await seed_year(owner_engine, cover.employee_id, "entitlement", "12")
    await make_login("hr")
    own = await submit(client, cover)  # manager -> HR queue, never in cover
    items = (await cover_list(client, cover)).json()["items"]
    assert [i["id"] for i in items] == [rid]
    assert own not in [i["id"] for i in items]
    # Not in the default list; the direct manager's own cover tab excludes their reports.
    assert (await cover_list(client, cover, "assigned")).json()["items"] == []
    assert (await cover_list(client, mgr)).json()["items"] == []


async def test_employee_cannot_open_cover(client: httpx.AsyncClient, staff) -> None:  # type: ignore[no-untyped-def]
    emp, _ = staff
    assert (await cover_list(client, emp)).status_code == 403


async def test_cover_approve_audit_and_email(
    client: httpx.AsyncClient,
    staff,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,  # type: ignore[no-untyped-def]
) -> None:
    emp, mgr = staff
    await seed_year(owner_engine, emp.employee_id, "entitlement", "7", type="sick")
    rid = await submit(client, emp, leave_type="sick", note="private note")
    cover = await make_login("manager")
    r = await decide(client, cover, rid, on_behalf_of=str(mgr.employee_id))
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert (
        await scalar(
            owner_engine, "SELECT decided_on_behalf_of FROM leave_request WHERE id = :i", i=rid
        )
        == mgr.employee_id
    )
    audit = (
        "SELECT count(*) FROM audit_log WHERE action = 'request.approve' AND actor_id = :a"
        " AND acting_for_id = :f AND detail::text NOT LIKE '%private%'"
    )
    assert await scalar(owner_engine, audit, a=cover.employee_id, f=mgr.employee_id) == 1
    body = await scalar(
        owner_engine,
        "SELECT body FROM email_outbox WHERE template = 'request_approved_on_behalf'"
        " AND recipient_employee_id = :m",
        m=mgr.employee_id,
    )
    assert isinstance(body, str) and "sick" not in body.lower() and "private" not in body


async def test_cover_reject_email_omits_reason(
    client: httpx.AsyncClient,
    staff,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,  # type: ignore[no-untyped-def]
) -> None:
    emp, mgr = staff
    rid = await submit(client, emp)
    cover = await make_login("manager")
    r = await decide(
        client, cover, rid, "reject", reason="zebra", on_behalf_of=str(mgr.employee_id)
    )
    assert r.status_code == 200
    body = await scalar(
        owner_engine,
        "SELECT body FROM email_outbox WHERE template = 'request_rejected_on_behalf'"
        " AND recipient_employee_id = :m",
        m=mgr.employee_id,
    )
    assert isinstance(body, str) and "zebra" not in body
    owner_mail = await scalar(
        owner_engine,
        "SELECT body FROM email_outbox WHERE template = 'request_rejected'"
        " AND recipient_employee_id = :e",
        e=emp.employee_id,
    )
    assert isinstance(owner_mail, str) and "zebra" in owner_mail


async def test_cover_authz(
    client: httpx.AsyncClient,
    staff,
    make_login: MakeLogin,  # type: ignore[no-untyped-def]
) -> None:
    emp, mgr = staff
    rid = await submit(client, emp)
    cover, wrong = await make_login("manager"), await make_login("manager")
    peer = await make_login()
    assert (await decide(client, peer, rid, on_behalf_of=str(mgr.employee_id))).status_code == 403
    mismatch = await decide(client, cover, rid, on_behalf_of=str(wrong.employee_id))
    assert mismatch.status_code == 403
    assert await status_of(client, mgr, rid) == "pending"
