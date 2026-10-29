from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.errors import ProblemError
from app.modules.balances import repository
from app.modules.leave_days.calendar import days_per_year
from app.modules.leave_days.service import working_half_days
from tests.conftest import MakeLogin


async def test_weekend_only_range_is_no_working_days(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(ProblemError) as err:
            await working_half_days(db, date(2026, 11, 7), "full", date(2026, 11, 8), "full")
    assert (err.value.status, err.value.code) == (422, "no_working_days")
    assert err.value.detail == "This range has no working days."


async def test_seeded_holiday_only_range_is_no_working_days(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(ProblemError) as err:
            await working_half_days(db, date(2026, 4, 27), "full", date(2026, 4, 27), "full")
    assert err.value.code == "no_working_days"


async def test_seeded_weekday_holiday_is_excluded(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        rows = await working_half_days(db, date(2026, 9, 2), "full", date(2026, 9, 4), "full")
    # Wed 2 Sep and Tue 1 Sep are holidays; Thu 3 and Fri 4 Sep are working days.
    assert [r[0] for r in rows] == [date(2026, 9, 3)] * 2 + [date(2026, 9, 4)] * 2


async def test_cross_year_split(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        rows = await working_half_days(db, date(2026, 12, 29), "full", date(2027, 1, 5), "full")
    assert days_per_year(rows) == {2026: Decimal(3), 2027: Decimal(2)}  # 1 Jan 2027 is a holiday


async def test_invalid_parts_are_422(app_engine: AsyncEngine) -> None:
    async with AsyncSession(app_engine) as db:
        with pytest.raises(ProblemError) as err:
            await working_half_days(db, date(2026, 11, 9), "am", date(2026, 11, 9), "pm")
    assert err.value.status == 422


async def test_days_for_reports_active_pending_and_approved_halves(
    app_engine: AsyncEngine, make_login: MakeLogin, make_request
) -> None:  # type: ignore[no-untyped-def]
    emp = (await make_login()).employee_id
    await make_request(emp, date(2026, 11, 2), date(2026, 11, 3), status="approved")
    await make_request(
        emp, date(2026, 11, 9), date(2026, 11, 9), status="pending", start_part="am", end_part="am"
    )
    await make_request(emp, date(2026, 11, 16), date(2026, 11, 16), status="rejected")
    await make_request(emp, date(2026, 11, 17), date(2026, 11, 17), status="cancelled")
    await make_request(emp, date(2026, 11, 18), date(2026, 11, 18), leave_type="sick")
    async with AsyncSession(app_engine) as db:
        days = await repository.days_for(db, emp, "annual", 2026)
        other_year = await repository.days_for(db, emp, "annual", 2027)
    assert sorted((d.leave_date, d.status) for d in days) == [
        (date(2026, 11, 2), "approved"),
        (date(2026, 11, 2), "approved"),
        (date(2026, 11, 3), "approved"),
        (date(2026, 11, 3), "approved"),
        (date(2026, 11, 9), "pending"),
    ]
    assert other_year == []


async def test_overlapping_active_half_day_is_refused_but_am_and_pm_coexist(
    owner_engine: AsyncEngine, make_login: MakeLogin, make_request
) -> None:  # type: ignore[no-untyped-def]
    emp = (await make_login()).employee_id
    day = date(2026, 11, 9)
    await make_request(emp, day, day, start_part="am", end_part="am")
    await make_request(emp, day, day, start_part="pm", end_part="pm")  # other slot: fine
    with pytest.raises(IntegrityError):
        await make_request(emp, day, day, start_part="am", end_part="am")
    # Once the first is inactive the slot is free again.
    other = (await make_login()).employee_id
    await make_request(other, day, day, status="cancelled")
    await make_request(other, day, day)


@pytest.mark.parametrize(
    "bad",
    [
        "end_date = '2026-11-01'",  # before start
        "working_days = 0",
        "working_days = 1.3",
        "start_part = 'am', end_date = '2026-11-03'",  # a multi-day request cannot start am
        "status = 'rejected'",  # needs a reason
        "decided_by = employee_id",
        "note = repeat('x', 501)",
    ],
)
async def test_leave_request_checks(
    owner_engine: AsyncEngine, make_login: MakeLogin, make_request, bad: str
) -> None:  # type: ignore[no-untyped-def]
    emp = (await make_login()).employee_id
    await make_request(emp, date(2026, 11, 2), date(2026, 11, 2))  # the baseline row is valid
    with pytest.raises((IntegrityError, DBAPIError)):
        async with owner_engine.connect() as conn:
            await conn.execute(
                text("UPDATE leave_request SET " + bad + " WHERE employee_id = :e"), {"e": emp}
            )


async def test_other_cancel_needs_a_reason(
    owner_engine: AsyncEngine, make_login: MakeLogin
) -> None:
    emp, hr = (await make_login()).employee_id, (await make_login("hr")).employee_id
    with pytest.raises((IntegrityError, DBAPIError)):
        async with owner_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO leave_request (employee_id, leave_type_code, start_date,"
                    " start_part, end_date, end_part, working_days, status, queue, cancelled_by)"
                    " VALUES (:e, 'annual', '2026-11-03', 'full', '2026-11-03', 'full', 1,"
                    " 'cancelled', 'manager', :c)"
                ),
                {"e": emp, "c": hr},
            )


async def test_weekend_day_row_is_refused(
    owner_engine: AsyncEngine, make_login: MakeLogin, make_request
) -> None:  # type: ignore[no-untyped-def]
    emp = (await make_login()).employee_id
    rid = await make_request(emp, date(2026, 11, 9), date(2026, 11, 9))
    with pytest.raises((IntegrityError, DBAPIError)):
        async with owner_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO leave_request_day (request_id, leave_date, slot, employee_id,"
                    " leave_year) VALUES (:r, '2026-11-07', 'am', :e, 2026)"
                ),
                {"r": rid, "e": emp},
            )


async def test_request_tables_are_not_deletable_and_anon_reads_nothing(
    owner_engine: AsyncEngine, app_engine: AsyncEngine, make_login: MakeLogin, make_request
) -> None:  # type: ignore[no-untyped-def]
    emp = (await make_login()).employee_id
    await make_request(emp, date(2026, 11, 9), date(2026, 11, 9))
    async with app_engine.connect() as conn:
        for table in ("leave_request", "leave_request_day"):
            with pytest.raises(DBAPIError):
                await conn.execute(text(f"DELETE FROM {table}"))
            await conn.rollback()
    async with owner_engine.connect() as conn:
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO anon"))
        await conn.execute(
            text("GRANT SELECT ON leave_request, leave_request_day, public_holiday TO anon")
        )
        await conn.execute(text("SET ROLE anon"))
        for table in ("leave_request", "leave_request_day", "public_holiday"):
            assert (await conn.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one() == 0
        await conn.execute(text("RESET ROLE"))
