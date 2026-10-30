import uuid
from datetime import date
from decimal import Decimal as D

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.errors import ProblemError
from app.modules.balances.me_router import get_today
from app.modules.balances.sufficiency import ensure_sufficient
from app.modules.identity.models import Employee
from tests.conftest import MakeLogin
from tests.modules.balances.test_ledger_jobs import seed_year

URL = "/api/v1/me/balances"
TODAY = date(2026, 6, 1)


async def _fixture(owner: AsyncEngine, emp: uuid.UUID, make_request) -> None:  # type: ignore[no-untyped-def]
    """12 entitlement + 3 carried - 4 used - 2 reserved = 9."""
    await seed_year(owner, emp, "entitlement", "12")
    await seed_year(owner, emp, "carry_over", "3", expires_on=date(2026, 12, 31))
    await make_request(emp, date(2026, 8, 3), date(2026, 8, 6), status="approved")  # 4 days
    await make_request(emp, date(2026, 9, 7), date(2026, 9, 8), status="pending")  # 2 days


async def test_requires_login(client: httpx.AsyncClient) -> None:
    assert (await client.get(URL)).status_code == 401


@pytest.fixture(autouse=True)
def fixed_today(app: FastAPI) -> None:
    app.dependency_overrides[get_today] = lambda: TODAY


@pytest.mark.parametrize("role", ["employee", "manager", "hr"])
async def test_display_fields_and_formula(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    make_request,  # type: ignore[no-untyped-def]
    role: str,
) -> None:
    me = await make_login(role)
    await _fixture(owner_engine, me.employee_id, make_request)
    await seed_year(owner_engine, me.employee_id, "entitlement", "7", type="sick")
    r = await client.get(URL, params={"year": 2026}, headers=me.headers)
    assert r.status_code == 200
    by = {b["leave_type"]: b for b in r.json()["balances"]}
    assert set(by) == {"annual", "sick"}  # Unpaid has none
    assert by["annual"] == {
        "leave_type": "annual",
        "entitlement": 12.0,
        "carried": 3.0,
        "expires_on": "2026-12-31",
        "carried_expired": False,
        "used": 4.0,
        "reserved": 2.0,
        "available": 9.0,
    }
    assert by["sick"]["expires_on"] is None


async def test_only_own_data_and_year_validated(
    client: httpx.AsyncClient,
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    make_request,  # type: ignore[no-untyped-def]
) -> None:
    me, mgr = await make_login(), await make_login("manager")
    await _fixture(owner_engine, me.employee_id, make_request)
    # An employee id is ignored: the manager only ever sees their own (empty) balances.
    params: dict[str, str | int] = {"year": 2026, "employee_id": str(me.employee_id)}
    other = (await client.get(URL, params=params, headers=mgr.headers)).json()
    assert all(b["entitlement"] == 0 and b["used"] == 0 for b in other["balances"])
    for bad in ("abc", "1999", "2101"):
        assert (await client.get(URL, params={"year": bad}, headers=me.headers)).status_code == 422


async def _check(owner: AsyncEngine, emp: uuid.UUID, code: str, requested: dict[int, D]) -> None:
    async with AsyncSession(owner) as db:
        employee = await db.get(Employee, emp)
        assert employee is not None
        await ensure_sufficient(db, employee, code, requested, TODAY)


async def test_boundary_exactly_zero_ok_and_shortfall_blocked(
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    make_request,  # type: ignore[no-untyped-def]
) -> None:
    me = await make_login()
    await seed_year(owner_engine, me.employee_id, "entitlement", "12")
    await make_request(me.employee_id, date(2026, 8, 3), date(2026, 8, 13), status="approved")  # 9
    await make_request(me.employee_id, date(2026, 9, 7), date(2026, 9, 7), status="pending")  # 1
    await _check(owner_engine, me.employee_id, "annual", {2026: D("2")})  # exactly zero
    with pytest.raises(ProblemError) as exc:
        await _check(owner_engine, me.employee_id, "annual", {2026: D("2.5")})
    assert exc.value.status == 422 and exc.value.code == "INSUFFICIENT_BALANCE"
    assert "0.5" in (exc.value.detail or "")


async def test_each_year_checked_and_carried_counts(
    make_login: MakeLogin, owner_engine: AsyncEngine
) -> None:
    me = await make_login()
    await seed_year(owner_engine, me.employee_id, "entitlement", "1", year=2026)
    await seed_year(owner_engine, me.employee_id, "carry_over", "1", expires_on=date(2026, 12, 31))
    await seed_year(owner_engine, me.employee_id, "entitlement", "1", year=2027)
    await _check(owner_engine, me.employee_id, "annual", {2026: D("2"), 2027: D("1")})
    with pytest.raises(ProblemError) as exc:
        await _check(owner_engine, me.employee_id, "annual", {2026: D("2"), 2027: D("1.5")})
    assert "2027" in (exc.value.detail or "")


async def test_unpaid_never_blocked(make_login: MakeLogin, owner_engine: AsyncEngine) -> None:
    me = await make_login()
    await _check(owner_engine, me.employee_id, "unpaid", {2026: D("200")})
