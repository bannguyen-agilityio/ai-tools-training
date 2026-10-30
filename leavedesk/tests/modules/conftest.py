import uuid
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.leave_days.calendar import Part, expand_days, working_days


@pytest.fixture
def make_request(owner_engine: AsyncEngine):  # type: ignore[no-untyped-def]
    """Insert a request and its day rows directly, as plan 10's submit will."""

    async def _make(
        employee_id: uuid.UUID,
        start: date,
        end: date,
        *,
        status: str = "approved",
        start_part: Part = "full",
        end_part: Part = "full",
        leave_type: str = "annual",
        holidays: frozenset[date] = frozenset(),
        active: bool | None = None,
    ) -> uuid.UUID:
        rid = uuid.uuid4()
        rows = expand_days(start, start_part, end, end_part, holidays)
        days = working_days(start, end, start_part, end_part, holidays)
        is_active = status in ("pending", "approved") if active is None else active
        async with owner_engine.connect() as conn:
            await conn.execute(
                text(
                    "INSERT INTO leave_request (id, employee_id, leave_type_code, start_date,"
                    " start_part, end_date, end_part, working_days, status, queue, decision_reason)"
                    " VALUES (:id, :e, :t, :s, :sp, :en, :ep, :wd, :st, 'manager',"
                    " CAST(:reason AS varchar))"
                ),
                {
                    "id": rid,
                    "e": employee_id,
                    "t": leave_type,
                    "s": start,
                    "sp": start_part,
                    "en": end,
                    "ep": end_part,
                    "wd": days,
                    "reason": "no" if status == "rejected" else None,
                    "st": status,
                },
            )
            for leave_date, slot, year in rows:
                await conn.execute(
                    text(
                        "INSERT INTO leave_request_day (request_id, leave_date, slot,"
                        " employee_id, leave_year, is_active) VALUES (:r, :d, :s, :e, :y, :a)"
                    ),
                    {
                        "r": rid,
                        "d": leave_date,
                        "s": slot,
                        "e": employee_id,
                        "y": year,
                        "a": is_active,
                    },
                )
        return rid

    return _make
