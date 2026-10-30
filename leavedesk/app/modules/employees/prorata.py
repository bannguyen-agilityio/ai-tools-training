"""New-joiner pro-rating (R9, Q2). Pure: no database, no clock."""

from datetime import date
from decimal import ROUND_FLOOR, Decimal

HALF = Decimal("0.5")
MID_MONTH_DAY = 15  # a start on day 1-15 counts that month


def round_half_up_to_half(value: Decimal) -> Decimal:
    """Nearest 0.5, ties up: 3.25 -> 3.5, 3.2 -> 3.0."""
    return ((value / HALF) + HALF).to_integral_value(rounding=ROUND_FLOOR) * HALF


def months_remaining(start: date) -> int:
    return 12 - (start.month - 1) - (1 if start.day > MID_MONTH_DAY else 0)


def prorata(start: date, entitlement: Decimal) -> Decimal:
    """Pro-rated days for the start year: entitlement x remaining months / 12, nearest 0.5."""
    return round_half_up_to_half(entitlement * months_remaining(start) / Decimal(12))
