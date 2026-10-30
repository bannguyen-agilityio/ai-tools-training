import uuid
from datetime import date
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import Login, MakeLogin

YEAR = date.today().year


def url(eid: uuid.UUID, tail: str = "") -> str:
    return f"/api/v1/hr/employees/{eid}/balance-entries{tail}"


def entry(**over: object) -> dict[str, object]:
    return {"leave_type_code": "annual", "kind": "opening", "days": 5, "leave_year": YEAR, **over}


async def rows(owner: AsyncEngine, sql: str, **params: object) -> list[dict[str, Any]]:
    async with owner.connect() as conn:
        return [dict(r) for r in (await conn.execute(text(sql), params)).mappings()]


async def post(
    client: httpx.AsyncClient, hr: Login, eid: uuid.UUID, tail: str = "", **over: object
) -> httpx.Response:
    return await client.post(url(eid, tail), json=entry(**over), headers=hr.mutating_headers)


# --- 401 / 403 matrix ----------------------------------------------------------------------


async def test_unauthenticated_is_401(client: httpx.AsyncClient) -> None:
    eid = uuid.uuid4()
    assert (await client.get("/api/v1/hr/balances")).status_code == 401
    assert (await client.get(f"/api/v1/hr/employees/{eid}/balances")).status_code == 401


@pytest.mark.parametrize("role", ["employee", "manager"])
async def test_non_hr_is_403_everywhere(
    client: httpx.AsyncClient, make_login: MakeLogin, role: str
) -> None:
    user = await make_login(role)
    eid = uuid.uuid4()
    h = user.mutating_headers
    calls = [
        client.get("/api/v1/hr/balances", headers=h),
        client.get(f"/api/v1/hr/employees/{eid}/balances", headers=h),
        client.post(url(eid, "/preview"), json=entry(), headers=h),
        client.post(url(eid), json=entry(), headers=h),
    ]
    for call in calls:
        assert (await call).status_code == 403


async def test_deputy_is_403(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    deputy = await make_login("employee")
    async with owner_engine.connect() as conn:
        await conn.execute(
            text("UPDATE employee SET is_hr_deputy = true WHERE id = :i"), {"i": deputy.employee_id}
        )
    assert (await client.get("/api/v1/hr/balances", headers=deputy.headers)).status_code == 403
    r = await post(client, deputy, uuid.uuid4())
    assert r.status_code == 403


# --- R24 entries ---------------------------------------------------------------------------


async def test_entry_saved_with_actor_time_and_audit(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    r = await post(client, hr, emp.employee_id, days=7.5)
    assert r.status_code == 201, r.text
    row = (await rows(owner_engine, "SELECT * FROM balance_entry WHERE id = :i", i=r.json()["id"]))[
        0
    ]
    assert row["created_by"] == hr.employee_id
    assert row["created_at"] is not None
    assert row["source"] == "manual"
    assert str(row["days"]) == "7.5"
    audit = await rows(
        owner_engine,
        "SELECT * FROM audit_log WHERE action = 'balance.entry_create' AND target_id = :t",
        t=str(row["id"]),
    )
    assert len(audit) == 1
    assert audit[0]["actor_id"] == hr.employee_id
    assert "reason" not in audit[0]["detail"]
    assert "leave_type_code" not in audit[0]["detail"]


@pytest.mark.parametrize("days", [0, 40])
async def test_range_edges_accepted(
    client: httpx.AsyncClient, make_login: MakeLogin, days: int
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    assert (await post(client, hr, emp.employee_id, days=days)).status_code == 201


@pytest.mark.parametrize("days", [41, -1, 40.5, 1.3])
@pytest.mark.parametrize("kind", ["opening", "carry_over"])
async def test_out_of_range_refused(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    days: float,
    kind: str,
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    extra = {"expires_on": f"{YEAR}-12-31"} if kind == "carry_over" else {}
    for tail in ("", "/preview"):
        r = await post(client, hr, emp.employee_id, tail, kind=kind, days=days, **extra)
        assert r.status_code == 422, r.text
    assert not await rows(
        owner_engine, "SELECT 1 FROM balance_entry WHERE employee_id = :e", e=emp.employee_id
    )


async def test_opening_sick_allowed_and_carry_over_rules(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    e = emp.employee_id
    assert (await post(client, hr, e, leave_type_code="sick", days=7)).status_code == 201
    ok = await post(client, hr, e, kind="carry_over", days=3, expires_on=f"{YEAR}-12-31")
    assert ok.status_code == 201
    assert (await post(client, hr, e, kind="carry_over", days=3)).status_code == 422
    bad_year = await post(client, hr, e, kind="carry_over", days=3, expires_on=f"{YEAR + 1}-12-31")
    assert bad_year.status_code == 422
    sick = await post(
        client, hr, e, kind="carry_over", leave_type_code="sick", days=1, expires_on=f"{YEAR}-12-31"
    )
    assert sick.status_code == 422
    assert (await post(client, hr, e, expires_on=f"{YEAR}-12-31")).status_code == 422


async def test_second_opening_is_409_and_huge_number_is_422(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    assert (await post(client, hr, emp.employee_id, days=5)).status_code == 201
    for tail in ("", "/preview"):
        assert (await post(client, hr, emp.employee_id, tail, days=5)).status_code == 409
    # Another type is a different balance, so it is still allowed.
    assert (await post(client, hr, emp.employee_id, leave_type_code="sick")).status_code == 201
    r = await client.post(
        url(emp.employee_id),
        content='{"leave_type_code":"annual","kind":"adjustment","days":1e999,"reason":"x"}',
        headers={**hr.mutating_headers, "Content-Type": "application/json"},
    )
    assert r.status_code == 422


async def test_unknown_employee_is_404(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr = await make_login("hr")
    assert (await post(client, hr, uuid.uuid4())).status_code == 404


# --- preview -------------------------------------------------------------------------------


async def test_preview_writes_nothing_and_returns_summary(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    await post(client, hr, emp.employee_id, days=4)
    before = await rows(owner_engine, "SELECT count(*) AS n FROM balance_entry")
    audits = await rows(owner_engine, "SELECT count(*) AS n FROM audit_log")
    r = await post(
        client, hr, emp.employee_id, "/preview", kind="adjustment", days=3, reason="check"
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["employee_id"] == str(emp.employee_id)
    assert body["kind"] == "adjustment"
    assert float(body["days"]) == 3
    assert float(body["resulting_available"]) == 7
    assert await rows(owner_engine, "SELECT count(*) AS n FROM balance_entry") == before
    assert await rows(owner_engine, "SELECT count(*) AS n FROM audit_log") == audits


# --- corrections ---------------------------------------------------------------------------


async def test_adjustment_needs_reason_and_keeps_original(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    first = (await post(client, hr, emp.employee_id, days=10)).json()
    no_reason = await post(client, hr, emp.employee_id, kind="adjustment", days=-2)
    assert no_reason.status_code == 422
    blank = await post(client, hr, emp.employee_id, kind="adjustment", days=-2, reason="  ")
    assert blank.status_code == 422
    fix = await post(
        client,
        hr,
        emp.employee_id,
        kind="adjustment",
        days=-2,
        reason="Typo at launch",
        corrects_entry_id=first["id"],
    )
    assert fix.status_code == 201, fix.text
    assert fix.json()["id"] != first["id"]
    original = (
        await rows(owner_engine, "SELECT days FROM balance_entry WHERE id = :i", i=first["id"])
    )[0]
    assert str(original["days"]) == "10.0"
    r = await client.get(
        f"/api/v1/hr/employees/{emp.employee_id}/balances?year={YEAR}", headers=hr.headers
    )
    annual = next(b for b in r.json()["balances"] if b["leave_type_code"] == "annual")
    assert float(annual["available"]) == 8


async def test_corrects_entry_of_another_employee_refused(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, a, b = await make_login("hr"), await make_login(), await make_login()
    other = (await post(client, hr, a.employee_id)).json()
    r = await post(
        client,
        hr,
        b.employee_id,
        kind="adjustment",
        days=1,
        reason="x",
        corrects_entry_id=other["id"],
    )
    assert r.status_code == 422


async def test_corrects_entry_of_another_type_refused(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    sick = (await post(client, hr, emp.employee_id, leave_type_code="sick", days=7)).json()
    r = await post(
        client,
        hr,
        emp.employee_id,
        kind="adjustment",
        days=-1,
        reason="x",
        corrects_entry_id=sick["id"],
    )
    assert r.status_code == 422


async def test_ledger_is_append_only_for_app_role(
    client: httpx.AsyncClient, make_login: MakeLogin, app_engine: AsyncEngine
) -> None:
    hr, emp = await make_login("hr"), await make_login()
    await post(client, hr, emp.employee_id)
    async with app_engine.connect() as conn:
        with pytest.raises(DBAPIError):
            await conn.execute(text("UPDATE balance_entry SET days = 1"))


# --- views ---------------------------------------------------------------------------------


async def test_ledger_view_newest_first(client: httpx.AsyncClient, make_login: MakeLogin) -> None:
    hr, emp = await make_login("hr"), await make_login()
    await post(client, hr, emp.employee_id, days=1)
    await post(client, hr, emp.employee_id, kind="adjustment", days=2, reason="later")
    r = await client.get(f"/api/v1/hr/employees/{emp.employee_id}/balances", headers=hr.headers)
    assert r.status_code == 200
    kinds = [e["kind"] for e in r.json()["ledger"]]
    assert kinds == ["adjustment", "opening"]


async def test_hr_list_has_all_active_employees(
    client: httpx.AsyncClient, make_login: MakeLogin
) -> None:
    hr, emp, gone = await make_login("hr"), await make_login(), await make_login(active=False)
    await post(client, hr, emp.employee_id, days=6)
    r = await client.get(f"/api/v1/hr/balances?year={YEAR}", headers=hr.headers)
    assert r.status_code == 200
    items = {i["employee_id"]: i for i in r.json()["items"]}
    assert str(emp.employee_id) in items
    assert str(hr.employee_id) in items
    assert str(gone.employee_id) not in items
    annual = next(
        b for b in items[str(emp.employee_id)]["balances"] if b["leave_type_code"] == "annual"
    )
    assert float(annual["available"]) == 6


async def test_manual_carry_over_is_capped_at_six_with_rollover(
    client: httpx.AsyncClient, make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    hr, emp, other = await make_login("hr"), await make_login(), await make_login()
    over = await post(
        client, hr, emp.employee_id, kind="carry_over", days=6.5, expires_on=f"{YEAR}-12-31"
    )
    assert over.status_code == 422
    six = await post(
        client, hr, emp.employee_id, kind="carry_over", days=6, expires_on=f"{YEAR}-12-31"
    )
    assert six.status_code == 201
    # A rollover carry already in the ledger counts toward the same cap.
    async with owner_engine.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO balance_entry (employee_id, leave_type_code, leave_year, kind, days,"
                " expires_on, source) VALUES (:e, 'annual', :y, 'carry_over', 4, :x, 'system')"
            ),
            {"e": other.employee_id, "y": YEAR, "x": date(YEAR, 12, 31)},
        )
        await conn.commit()
    stacked = await post(
        client, hr, other.employee_id, kind="carry_over", days=3, expires_on=f"{YEAR}-12-31"
    )
    assert stacked.status_code == 409
    fits = await post(
        client, hr, other.employee_id, kind="carry_over", days=2, expires_on=f"{YEAR}-12-31"
    )
    assert fits.status_code == 201
