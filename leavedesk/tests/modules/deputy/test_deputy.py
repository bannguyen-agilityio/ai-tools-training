import re
import uuid

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin
from tests.modules.approvals.test_approvals import decide
from tests.modules.balances.test_ledger_jobs import seed_year
from tests.modules.employees.test_employees import rows
from tests.modules.requests.test_requests import body, post

URL = "/api/v1/hr/deputy"


async def put(client: httpx.AsyncClient, who: Login, employee_id: object) -> httpx.Response:
    return await client.put(URL, json={"employee_id": employee_id}, headers=who.mutating_headers)


async def deputy_ids(owner: AsyncEngine) -> list[uuid.UUID]:
    found = await rows(owner, "SELECT id FROM employee WHERE is_hr_deputy")
    return [r["id"] for r in found]


async def test_requires_session_and_csrf(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    assert (await client.get(URL)).status_code == 401
    assert (await client.put(URL, json={"employee_id": None})).status_code == 401
    r = await client.put(URL, json={"employee_id": None}, headers=hr.headers)
    assert r.status_code == 403


async def test_only_hr_admin_may_read_or_assign(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    target, deputy = await make_login(), await make_login()
    await put(client, await make_login("hr"), str(deputy.employee_id))
    for who in (await make_login(), await make_login("manager"), deputy):
        assert (await client.get(URL, headers=who.headers)).status_code == 403
        assert (await put(client, who, str(target.employee_id))).status_code == 403
    assert await deputy_ids(owner_engine) == [deputy.employee_id]


async def test_assign_replace_clear_and_audit(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, a, b = await make_login("hr"), await make_login(), await make_login("manager")
    assert (await client.get(URL, headers=hr.headers)).json()["employee_id"] is None
    r = await put(client, hr, str(a.employee_id))
    assert r.status_code == 200 and r.json()["employee_id"] == str(a.employee_id)
    assert (await client.get(URL, headers=hr.headers)).json()["employee_id"] == str(a.employee_id)
    # A second deputy replaces the first: never two at once.
    assert (await put(client, hr, str(b.employee_id))).status_code == 200
    assert await deputy_ids(owner_engine) == [b.employee_id]
    assert (await put(client, hr, None)).json()["employee_id"] is None
    assert await deputy_ids(owner_engine) == []
    audits = await rows(
        owner_engine,
        "SELECT actor_id, detail::text AS d FROM audit_log WHERE action = 'employee.role_change'",
    )
    assert len(audits) == 3 and all(x["actor_id"] == hr.employee_id for x in audits)


async def test_role_and_state_guards(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr = await make_login("hr")
    other_hr, gone = await make_login("hr"), await make_login(active=False)
    for target in (str(other_hr.employee_id), str(gone.employee_id), str(uuid.uuid4())):
        assert (await put(client, hr, target)).status_code == 422
    assert (await client.put(URL, json={}, headers=hr.mutating_headers)).status_code == 422
    r = await client.put(URL, json={"employee_id": None, "x": 1}, headers=hr.mutating_headers)
    assert r.status_code == 400
    assert await deputy_ids(owner_engine) == []


async def test_hr_admin_leave_goes_to_the_deputy_and_hr_cannot_decide_it(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, other_hr, deputy = await make_login("hr"), await make_login("hr"), await make_login()
    await seed_year(owner_engine, hr.employee_id, "entitlement", "12")
    no_deputy = await post(client, hr, body("2026-06-08"))
    assert no_deputy.status_code == 422 and no_deputy.json()["error"]["code"] == "NO_APPROVER"
    await put(client, other_hr, str(deputy.employee_id))

    r = await post(client, hr, body("2026-06-08"))
    assert r.status_code == 201, r.text
    got = r.json()
    assert (got["queue"], got["assigned_to"]) == ("deputy", str(deputy.employee_id))
    emails = await rows(
        owner_engine,
        "SELECT recipient_employee_id FROM email_outbox WHERE template = 'request_created'",
    )
    assert [e["recipient_employee_id"] for e in emails] == [deputy.employee_id]

    # No HR admin decides it (the requester or a colleague); the deputy does, and is the actor.
    assert (await decide(client, hr, got["id"])).status_code == 403
    assert (await decide(client, other_hr, got["id"])).status_code == 403
    queue = await client.get("/api/v1/approvals?scope=assigned", headers=deputy.headers)
    assert [i["id"] for i in queue.json()["items"]] == [got["id"]]
    mine = await client.get("/api/v1/approvals?scope=assigned", headers=other_hr.headers)
    assert mine.json()["items"] == []
    assert (await decide(client, deputy, got["id"])).status_code == 200
    actor = await rows(
        owner_engine, "SELECT actor_id FROM audit_log WHERE action = 'request.approve'"
    )
    assert [a["actor_id"] for a in actor] == [deputy.employee_id]


async def test_deputy_decides_a_managers_request(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, deputy, mgr = await make_login("hr"), await make_login(), await make_login("manager")
    await seed_year(owner_engine, mgr.employee_id, "entitlement", "12")
    await put(client, hr, str(deputy.employee_id))
    rid = (await post(client, mgr, body("2026-06-08"))).json()["id"]
    assert (await decide(client, deputy, rid)).status_code == 200
    actor = await rows(
        owner_engine, "SELECT actor_id FROM audit_log WHERE action = 'request.approve'"
    )
    assert [a["actor_id"] for a in actor] == [deputy.employee_id]


async def test_deputy_is_refused_on_every_hr_route(
    app: FastAPI, client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    """Generated from the route table, so a new `/hr/` route is covered without editing this."""
    hr, deputy, mgr = await make_login("hr"), await make_login(), await make_login("manager")
    await put(client, hr, str(deputy.employee_id))
    calls = [
        (method.upper(), path)
        for path, item in app.openapi()["paths"].items()
        if path.startswith("/api/v1/hr/")
        for method in item
    ]
    assert len(calls) >= 10  # guards against the filter silently matching nothing
    for who in (deputy, mgr):
        for method, path in calls:
            filled = re.sub(r"\{[^}]+\}", lambda _: str(uuid.uuid4()), path)
            r = await client.request(method, filled, json={}, headers=who.mutating_headers)
            assert r.status_code == 403, (method, path, r.status_code)


async def test_clearing_the_deputy_is_refused_while_hr_leave_waits_for_them(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, deputy, other = await make_login("hr"), await make_login(), await make_login()
    await seed_year(owner_engine, hr.employee_id, "entitlement", "12")
    await put(client, hr, str(deputy.employee_id))
    rid = (await post(client, hr, body("2026-06-08"))).json()["id"]
    r = await put(client, hr, None)
    assert r.status_code == 409 and r.json()["error"]["code"] == "DEPUTY_HAS_PENDING"
    assert await deputy_ids(owner_engine) == [deputy.employee_id]
    # Replacing is fine: the new deputy can decide the waiting request.
    assert (await put(client, hr, str(other.employee_id))).status_code == 200
    assert (await decide(client, other, rid)).status_code == 200
    assert (await put(client, hr, None)).status_code == 200


async def test_cancelled_hr_leave_notifies_only_the_deputy(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, other_hr, deputy = await make_login("hr"), await make_login("hr"), await make_login()
    await seed_year(owner_engine, hr.employee_id, "entitlement", "12")
    await put(client, other_hr, str(deputy.employee_id))
    rid = (await post(client, hr, body("2026-06-08"))).json()["id"]
    r = await post(client, hr, {"version": 1}, f"/api/v1/requests/{rid}/cancel")
    assert r.status_code == 200
    sent = await rows(
        owner_engine,
        "SELECT recipient_employee_id FROM email_outbox "
        "WHERE template = 'request_cancelled_by_employee'",
    )
    assert [s["recipient_employee_id"] for s in sent] == [deputy.employee_id]


async def test_deputy_cannot_be_promoted_to_hr_by_patch(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, deputy = await make_login("hr"), await make_login()
    await put(client, hr, str(deputy.employee_id))
    r = await client.patch(
        f"/api/v1/hr/employees/{deputy.employee_id}",
        json={"role": "hr"},
        headers=hr.mutating_headers,
    )
    assert r.status_code == 422
