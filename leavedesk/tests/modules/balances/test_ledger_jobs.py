import uuid
from datetime import date
from decimal import Decimal as D

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.modules.balances import repository, service
from app.modules.balances.compute import DayUse
from tests.conftest import MakeLogin


async def seed_year(owner: AsyncEngine, emp: uuid.UUID, kind: str, days: str, **kw: object) -> None:
    async with owner.connect() as conn:
        await conn.execute(
            text(
                "INSERT INTO balance_entry (employee_id, leave_type_code, leave_year, kind, days,"
                " expires_on) VALUES (:e, :t, :y, :k, :d, :x)"
            ),
            {
                "e": emp,
                "t": kw.get("type", "annual"),
                "y": kw.get("year", 2026),
                "k": kind,
                "d": D(days),
                "x": kw.get("expires_on"),
            },
        )


def used(n: int):  # type: ignore[no-untyped-def]
    """Loader reporting n full approved days in the previous year."""

    async def load(db, emp, code, year):  # type: ignore[no-untyped-def]
        return [DayUse(date(year, 6, 1 + i // 2), "approved") for i in range(n * 2)]

    return load


async def all_entries(owner: AsyncEngine) -> list[dict]:  # type: ignore[type-arg]
    async with owner.connect() as conn:
        rows = await conn.execute(
            text("SELECT * FROM balance_entry ORDER BY leave_type_code, kind, leave_year")
        )
        return [dict(r) for r in rows.mappings()]


async def test_leave_types_seeded(owner_engine: AsyncEngine) -> None:
    async with owner_engine.connect() as conn:
        rows = (await conn.execute(text("SELECT * FROM leave_type"))).mappings().all()
    by = {r["code"]: r for r in rows}
    assert by["annual"]["annual_allowance"] == D(12) and by["annual"]["carry_cap"] == D(6)
    assert by["sick"]["annual_allowance"] == D(7) and not by["sick"]["carries_over"]
    assert by["unpaid"]["annual_allowance"] is None and not by["unpaid"]["is_limited"]


@pytest.mark.parametrize(("taken", "carried"), [(8, 4), (3, 6), (0, 6), (12, 0)])
async def test_rollover_carries_min_6_unused(
    make_login: MakeLogin,
    owner_engine: AsyncEngine,
    app_engine: AsyncEngine,
    taken: int,
    carried: int,
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "12")
    async with AsyncSession(app_engine) as db:
        await service.rollover(db, 2027, used(taken))
    rows = await all_entries(owner_engine)
    carry = [r for r in rows if r["kind"] == "carry_over"]
    if carried:
        assert [(r["days"], r["expires_on"], r["leave_year"]) for r in carry] == [
            (D(carried), date(2027, 12, 31), 2027)
        ]
    else:
        assert carry == []
    # new year entitlement for Annual 12 and Sick 7
    ent = {
        (r["leave_type_code"], r["days"])
        for r in rows
        if r["leave_year"] == 2027 and r["kind"] == "entitlement"
    }
    assert ent == {("annual", D(12)), ("sick", D(7))}


async def test_sick_never_carries(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "7", type="sick")
    async with AsyncSession(app_engine) as db:
        await service.rollover(db, 2027, used(0))
    assert [r for r in await all_entries(owner_engine) if r["kind"] == "carry_over"] == []


async def test_no_recarry_of_carried_block(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "12", year=2027)
    await seed_year(owner_engine, emp, "carry_over", "6", year=2027, expires_on=date(2027, 12, 31))
    async with AsyncSession(app_engine) as db:
        await service.rollover(db, 2028, used(0))
    carry = [
        r
        for r in await all_entries(owner_engine)
        if r["leave_year"] == 2028 and r["kind"] == "carry_over"
    ]
    assert [r["days"] for r in carry] == [D(6)]  # 12 unused entitlement capped, not 12 + 6


async def test_rollover_idempotent(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "12")
    async with AsyncSession(app_engine) as db:
        first = await service.rollover(db, 2027, used(8))
    before = await all_entries(owner_engine)
    async with AsyncSession(app_engine) as db:
        second = await service.rollover(db, 2027, used(8))
    assert first == 3 and second == 0
    assert await all_entries(owner_engine) == before


async def test_new_joiner_gets_no_full_entitlement(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    await make_login()
    async with owner_engine.connect() as conn:
        await conn.execute(text("UPDATE employee SET start_date = '2027-03-01'"))
    async with AsyncSession(app_engine) as db:
        await service.rollover(db, 2027, used(0))
    assert await all_entries(owner_engine) == []  # prorata is written on save (R9)


async def test_expire_carry_writes_once(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "12", year=2027)
    await seed_year(owner_engine, emp, "carry_over", "4", year=2027, expires_on=date(2027, 12, 31))
    async with AsyncSession(app_engine) as db:
        assert await service.expire_carry(db, date(2027, 12, 31), used(0)) == 0  # not yet expired
    async with AsyncSession(app_engine) as db:
        assert await service.expire_carry(db, date(2028, 1, 1), used(0)) == 1
    async with AsyncSession(app_engine) as db:
        assert await service.expire_carry(db, date(2028, 1, 2), used(0)) == 0
    expiry = [r for r in await all_entries(owner_engine) if r["kind"] == "expiry"]
    assert [(r["days"], r["leave_year"]) for r in expiry] == [(D(-4), 2027)]


async def test_idempotency_key_conflict_returns_false(
    make_login: MakeLogin, app_engine: AsyncEngine
) -> None:
    emp = (await make_login()).employee_id
    args = dict(
        employee_id=emp,
        leave_type_code="annual",
        leave_year=2027,
        kind="entitlement",
        days=D(12),
        idempotency_key="k",
    )
    async with AsyncSession(app_engine) as db:
        assert await repository.add_entry(db, **args) is True  # type: ignore[arg-type]
        assert await repository.add_entry(db, **args) is False  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "sql",
    ["UPDATE balance_entry SET days = 1", "DELETE FROM balance_entry", "TRUNCATE balance_entry"],
)
async def test_app_role_cannot_modify_ledger(
    make_login: MakeLogin, owner_engine: AsyncEngine, app_engine: AsyncEngine, sql: str
) -> None:
    emp = (await make_login()).employee_id
    await seed_year(owner_engine, emp, "entitlement", "12")
    async with AsyncSession(app_engine) as db:
        with pytest.raises(ProgrammingError):
            await db.execute(text(sql))


@pytest.mark.parametrize(
    ("kind", "days", "type_code"),
    [
        ("entitlement", "0.3", "annual"),  # not a 0.5 step
        ("adjustment", "1", "annual"),  # reason required
        ("entitlement", "5", "unpaid"),  # unpaid has no balance
        ("carry_over", "2", "annual"),  # carry_over needs expires_on
        ("entitlement", "-1", "annual"),  # credits cannot be negative
        ("expiry", "1", "annual"),  # expiry cannot add days
    ],
)
async def test_db_checks_reject(
    make_login: MakeLogin, owner_engine: AsyncEngine, kind: str, days: str, type_code: str
) -> None:
    emp = (await make_login()).employee_id
    with pytest.raises((IntegrityError, DBAPIError)):
        await seed_year(owner_engine, emp, kind, days, type=type_code)


async def test_anon_reads_nothing(owner_engine: AsyncEngine) -> None:
    async with owner_engine.connect() as conn:
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO anon"))
        await conn.execute(text("GRANT SELECT ON balance_entry, leave_type TO anon"))
        await conn.execute(text("SET ROLE anon"))
        for table in ("balance_entry", "leave_type"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0
        await conn.execute(text("RESET ROLE"))


async def test_days_for_refuses_until_leave_days_exist(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(NotImplementedError):
            await repository.days_for(db, uuid.uuid4(), "annual", 2026)


def test_rollover_year_is_never_in_the_future() -> None:
    from app.jobs.rollover import resolve_year

    assert resolve_year([], 2027) == 2027
    assert resolve_year(["2026"], 2027) == 2026
    with pytest.raises(ValueError):
        resolve_year(["2028"], 2027)
    with pytest.raises(ValueError):
        resolve_year(["20x7"], 2027)
