from datetime import date
from decimal import Decimal as D

import pytest

from app.modules.balances.compute import Balance, DayUse, Entry, compute_balance

TODAY = date(2027, 3, 1)
EXP = date(2027, 12, 31)


def e(kind: str, days: str, expires_on: date | None = None) -> Entry:
    return Entry(kind=kind, days=D(days), expires_on=expires_on)  # type: ignore[arg-type]


def d(iso: str, status: str = "approved") -> DayUse:
    return DayUse(leave_date=date.fromisoformat(iso), status=status)  # type: ignore[arg-type]


def full_day(iso: str, status: str = "approved") -> list[DayUse]:
    return [d(iso, status), d(iso, status)]


def test_empty_ledger_is_zero() -> None:
    assert compute_balance([], [], TODAY) == Balance(D(0), D(0), D(0), D(0), D(0), D(0))


@pytest.mark.parametrize(
    ("entries", "days", "used", "reserved", "avail"),
    [
        # half days are 0.5 each
        ([e("entitlement", "12")], [d("2027-03-02"), d("2027-03-03")], 1, 0, 11),
        # Pending reserves
        ([e("entitlement", "12")], [d("2027-03-02", "pending")], 0, 0.5, 11.5),
        # several entitlement kinds, signed adjustments
        (
            [e("opening", "3"), e("prorata", "4.5"), e("adjustment", "-1"), e("adjustment", "2")],
            [],
            0,
            0,
            8.5,
        ),
        # expired by expires_on although the expiry job has not run
        ([e("entitlement", "12"), e("carry_over", "4", date(2027, 2, 28))], [], 0, 0, 12),
        # the expiry entry is a record only: not subtracted a second time
        (
            [e("entitlement", "12"), e("carry_over", "4", date(2027, 2, 28)), e("expiry", "-4")],
            [],
            0,
            0,
            12,
        ),
    ],
)
def test_table(entries, days, used, reserved, avail) -> None:  # type: ignore[no-untyped-def]
    b = compute_balance(entries, days, TODAY)
    assert (b.used, b.reserved, b.available) == (D(str(used)), D(str(reserved)), D(str(avail)))


def test_carried_first_then_entitlement() -> None:
    # R7: 2 carried + 10 current, 3 days approved
    entries = [e("entitlement", "10"), e("carry_over", "2", EXP)]
    days = full_day("2027-03-02") + full_day("2027-03-03") + full_day("2027-03-04")
    b = compute_balance(entries, days, TODAY)
    assert b.used == D(3)
    assert b.carried_remaining == D(0)
    assert b.entitlement_remaining == D(9)
    assert b.available == D(9)


def test_leave_after_expires_on_draws_on_entitlement() -> None:
    entries = [e("entitlement", "12"), e("carry_over", "4", date(2027, 1, 31))]
    b = compute_balance(entries, full_day("2027-02-02"), date(2027, 1, 15))
    assert b.carried_remaining == D(4)
    assert b.entitlement_remaining == D(11)
    assert b.available == D(15)


def test_carried_excluded_once_today_is_past_expires_on() -> None:
    entries = [e("entitlement", "12"), e("carry_over", "4", date(2027, 1, 31))]
    b = compute_balance(entries, [], date(2027, 2, 1))
    assert b.carried_remaining == D(0)
    assert b.available == D(12)
    assert b.expirable_carried == D(4)


def test_leave_on_expiry_day_still_uses_carried() -> None:
    entries = [e("entitlement", "12"), e("carry_over", "4", date(2027, 1, 31))]
    b = compute_balance(entries, full_day("2027-01-31"), date(2027, 1, 20))
    assert b.carried_remaining == D(3)
    assert b.entitlement_remaining == D(12)


def test_earliest_expiring_block_is_used_first() -> None:
    entries = [e("carry_over", "2", date(2028, 12, 31)), e("carry_over", "1", EXP)]
    b = compute_balance(entries, full_day("2027-03-02"), TODAY)
    assert b.used == D(1)
    assert b.carried_remaining == D(2)


def test_half_day_leaves_half_of_carried() -> None:
    b = compute_balance([e("carry_over", "1", EXP)], [d("2027-03-02")], TODAY)
    assert b.carried_remaining == D("0.5")


def test_unused_entitlement_ignores_carried_block() -> None:
    # R7 no re-carry: 5 days all taken from the 6 carried, 12 current-year still unused
    entries = [e("entitlement", "12"), e("carry_over", "6", EXP)]
    days = [x for i in range(2, 7) for x in full_day(f"2027-03-0{i}")]
    assert compute_balance(entries, days, TODAY).unused_entitlement == D(12)


def test_unused_entitlement_counts_pending_as_consumed() -> None:
    b = compute_balance([e("entitlement", "12")], full_day("2027-12-30", "pending"), TODAY)
    assert b.unused_entitlement == D(11)


def test_overdrawn_unused_floors_at_zero() -> None:
    days = full_day("2027-03-02") + full_day("2027-03-03")
    b = compute_balance([e("entitlement", "1")], days, TODAY)
    assert b.unused_entitlement == D(0)
    assert b.available == D(-1)
