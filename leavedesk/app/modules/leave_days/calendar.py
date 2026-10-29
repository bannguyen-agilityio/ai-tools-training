"""Working-day expansion (spec 5.1, R6). Pure: dates only, no DB, no clock, no time zone.

Callers pass `date`s already resolved in `COMPANY_TZ`. A working day is Mon-Fri that is not a
public holiday; a full day is two half-day rows (`am`, `pm`), matching `leave_request_day`.
"""

from collections import defaultdict
from collections.abc import Collection, Iterable
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

Part = Literal["full", "am", "pm"]
Slot = Literal["am", "pm"]
# (leave_date, slot, leave_year)
HalfDay = tuple[date, Slot, int]

HALF = Decimal("0.5")
SATURDAY = 5  # date.weekday(): Mon=0 ... Sun=6


def _check_parts(start: date, start_part: Part, end: date, end_part: Part) -> None:
    """The R12/Q7 shape rules, so a bad combination cannot silently count wrong days."""
    if end < start:
        raise ValueError("end before start")
    if start == end:
        if start_part != end_part:
            raise ValueError("a single-day request needs the same start and end part")
    elif start_part == "am" or end_part == "pm":
        raise ValueError("a multi-day request starts full or pm and ends full or am")


def _slots(day: date, start: date, start_part: Part, end: date, end_part: Part) -> tuple[Slot, ...]:
    first = start_part if day == start else "full"
    last = end_part if day == end else "full"
    if first == "pm" or last == "pm":
        return ("pm",)
    if first == "am" or last == "am":
        return ("am",)
    return ("am", "pm")


def expand_days(
    start: date, start_part: Part, end: date, end_part: Part, holidays: Collection[date]
) -> list[HalfDay]:
    """Every working half day of the range, in date order. Empty when none (weekend/holiday)."""
    _check_parts(start, start_part, end, end_part)
    rows: list[HalfDay] = []
    day = start
    while day <= end:
        if day.weekday() < SATURDAY and day not in holidays:
            rows.extend(
                (day, slot, day.year) for slot in _slots(day, start, start_part, end, end_part)
            )
        day += timedelta(days=1)
    return rows


def days_per_year(rows: Iterable[HalfDay]) -> dict[int, Decimal]:
    """Working days per leave year: a cross-year request deducts per year (R6)."""
    totals: dict[int, Decimal] = defaultdict(Decimal)
    for _, _, year in rows:
        totals[year] += HALF
    return dict(totals)


def working_days(
    start: date,
    end: date,
    start_part: Part = "full",
    end_part: Part = "full",
    holidays: Collection[date] = frozenset(),
) -> Decimal:
    return HALF * len(expand_days(start, start_part, end, end_part, holidays))
