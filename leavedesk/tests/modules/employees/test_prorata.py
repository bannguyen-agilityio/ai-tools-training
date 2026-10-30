from datetime import date
from decimal import Decimal

import pytest

from app.modules.employees.prorata import months_remaining, prorata, round_half_up_to_half


@pytest.mark.parametrize(
    ("start", "annual", "sick"),
    [
        (date(2026, 7, 1), "6.0", "3.5"),
        (date(2026, 7, 15), "6.0", "3.5"),  # day 15 counts July
        (date(2026, 7, 16), "5.0", "3.0"),  # day 16 does not
        (date(2026, 1, 1), "12.0", "7.0"),
        (date(2026, 12, 16), "0.0", "0.0"),
    ],
)
def test_prorata_table(start: date, annual: str, sick: str) -> None:
    assert prorata(start, Decimal(12)) == Decimal(annual)
    assert prorata(start, Decimal(7)) == Decimal(sick)


def test_months_remaining() -> None:
    assert months_remaining(date(2026, 7, 1)) == 6
    assert months_remaining(date(2026, 7, 16)) == 5


@pytest.mark.parametrize(
    ("value", "expected"),
    [("3.25", "3.5"), ("3.2", "3.0"), ("3.75", "4.0"), ("3.0", "3.0"), ("3.5", "3.5")],
)
def test_round_half_up(value: str, expected: str) -> None:
    assert round_half_up_to_half(Decimal(value)) == Decimal(expected)
