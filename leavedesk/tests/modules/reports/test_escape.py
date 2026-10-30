from datetime import date
from decimal import Decimal

import pytest

from app.modules.reports.escape import escape_cell


@pytest.mark.parametrize("lead", ["=", "+", "-", "@", "\t", "\r"])
def test_dangerous_text_is_prefixed(lead: str) -> None:
    for tail in ("SUM(A1:A9)", "cmd|' /C calc'!A0", "1+1", "", " leading space"):
        assert escape_cell(lead + tail) == "'" + lead + tail


@pytest.mark.parametrize(
    "text", ["Ann", "Annual", "a=b", "x-ray", "", "'=quoted", " plain text", "2026-06-08"]
)
def test_safe_text_is_unchanged(text: str) -> None:
    assert escape_cell(text) == text


@pytest.mark.parametrize("text", [" =SUM(A1)", "\n+1", "  @x", " \t-1"])
def test_leading_whitespace_does_not_hide_a_formula(text: str) -> None:
    assert escape_cell(text) == "'" + text


def test_numbers_dates_and_none_are_never_touched() -> None:
    for value in (-1, 0, 3.5, -0.5, Decimal("-1.5"), Decimal("2.0"), date(2026, 6, 8), None):
        assert escape_cell(value) is value
