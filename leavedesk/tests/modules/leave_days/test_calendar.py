from datetime import date
from decimal import Decimal

import pytest

from app.modules.leave_days.calendar import days_per_year, expand_days, working_days

NO_HOLIDAYS: frozenset[date] = frozenset()


def test_fri_to_mon_is_two_days() -> None:
    assert working_days(date(2026, 11, 6), date(2026, 11, 9)) == 2.0


def test_weekday_holiday_is_excluded() -> None:
    # Wed 2 Sep 2026 is National Day.
    assert working_days(date(2026, 9, 1), date(2026, 9, 3), holidays={date(2026, 9, 2)}) == 2


def test_holiday_on_a_weekend_changes_nothing() -> None:
    sat = date(2026, 11, 7)
    assert working_days(date(2026, 11, 6), date(2026, 11, 9), holidays={sat}) == 2


def test_weekend_only_and_holiday_only_ranges_are_empty() -> None:
    assert expand_days(date(2026, 11, 7), "full", date(2026, 11, 8), "full", NO_HOLIDAYS) == []
    day = date(2026, 9, 2)
    assert expand_days(day, "full", day, "full", {day}) == []
    assert working_days(day, day, holidays={day}) == 0


def test_full_day_is_two_half_day_rows() -> None:
    rows = expand_days(date(2026, 11, 9), "full", date(2026, 11, 9), "full", NO_HOLIDAYS)
    assert rows == [(date(2026, 11, 9), "am", 2026), (date(2026, 11, 9), "pm", 2026)]


@pytest.mark.parametrize(("part", "slots"), [("am", ["am"]), ("pm", ["pm"])])
def test_single_half_day(part: str, slots: list[str]) -> None:
    day = date(2026, 11, 9)
    rows = expand_days(day, part, day, part, NO_HOLIDAYS)  # type: ignore[arg-type]
    assert [r[1] for r in rows] == slots
    assert working_days(day, day, start_part=part, end_part=part) == Decimal("0.5")  # type: ignore[arg-type]


def test_starts_in_the_afternoon_and_ends_in_the_morning() -> None:
    # Fri pm, Mon am: 0.5 + 0.5.
    rows = expand_days(date(2026, 11, 6), "pm", date(2026, 11, 9), "am", NO_HOLIDAYS)
    assert rows == [(date(2026, 11, 6), "pm", 2026), (date(2026, 11, 9), "am", 2026)]
    assert working_days(date(2026, 11, 6), date(2026, 11, 9), "pm", "am") == 1


def test_start_part_on_a_holiday_is_dropped() -> None:
    thu, fri = date(2026, 11, 5), date(2026, 11, 6)
    assert working_days(thu, fri, "pm", "full", holidays={thu}) == 1


def test_cross_year_is_split_per_leave_year() -> None:
    # Tue 29 Dec 2026 to Tue 5 Jan 2027: 29, 30, 31 Dec (3) + 1 Jan holiday, 4, 5 Jan (2).
    rows = expand_days(date(2026, 12, 29), "full", date(2027, 1, 5), "full", {date(2027, 1, 1)})
    assert days_per_year(rows) == {2026: Decimal(3), 2027: Decimal(2)}


def test_31_dec_to_2_jan() -> None:
    rows = expand_days(date(2026, 12, 31), "full", date(2027, 1, 2), "full", NO_HOLIDAYS)
    # Thu 31 Dec, Fri 1 Jan; Sat 2 Jan is a weekend.
    assert days_per_year(rows) == {2026: Decimal(1), 2027: Decimal(1)}


@pytest.mark.parametrize(
    ("start", "sp", "end", "ep"),
    [
        (date(2026, 11, 9), "full", date(2026, 11, 6), "full"),  # end before start
        (date(2026, 11, 9), "am", date(2026, 11, 9), "pm"),  # single day, parts differ
        (date(2026, 11, 6), "am", date(2026, 11, 9), "full"),  # multi-day must start full/pm
        (date(2026, 11, 6), "full", date(2026, 11, 9), "pm"),  # multi-day must end full/am
    ],
)
def test_invalid_part_combinations_are_refused(start: date, sp: str, end: date, ep: str) -> None:
    with pytest.raises(ValueError):
        expand_days(start, sp, end, ep, NO_HOLIDAYS)  # type: ignore[arg-type]
