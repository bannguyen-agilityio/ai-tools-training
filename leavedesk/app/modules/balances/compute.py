"""The only place balance rules live (spec 5.4, R5, R7, R8). Pure: no DB, no clock."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

EntryKind = Literal["opening", "entitlement", "prorata", "carry_over", "expiry", "adjustment"]
DayStatus = Literal["approved", "pending"]

HALF = Decimal("0.5")
ENTITLEMENT_KINDS = frozenset({"opening", "entitlement", "prorata", "adjustment"})


@dataclass(frozen=True)
class Entry:
    kind: EntryKind
    days: Decimal
    expires_on: date | None = None


@dataclass(frozen=True)
class DayUse:
    """One active half day of a request (a `leave_request_day` row)."""

    leave_date: date
    status: DayStatus


@dataclass(frozen=True)
class Balance:
    entitlement_remaining: Decimal
    carried_remaining: Decimal  # unexpired as of `today`
    used: Decimal
    reserved: Decimal
    unused_entitlement: Decimal  # rollover input: entitlement left, never carried days
    expirable_carried: Decimal  # unused carried days whose block is past expires_on

    @property
    def available(self) -> Decimal:
        return self.entitlement_remaining + self.carried_remaining


@dataclass
class _Block:
    expires_on: date
    left: Decimal


def compute_balance(entries: Iterable[Entry], days: Iterable[DayUse], today: date) -> Balance:
    """Balance for one employee, leave type and leave year.

    Days are taken from the carried blocks first (earliest expiry first) while the block is
    unexpired on the leave date, then from entitlement. `expiry` entries are a record only:
    expiry is derived from `expires_on`, so a lagging job never changes the balance.
    A-7: Pending reservations count as consumed when working out unused entitlement.
    """
    entries = list(entries)
    entitlement = sum((x.days for x in entries if x.kind in ENTITLEMENT_KINDS), Decimal(0))
    blocks = sorted(
        (_Block(x.expires_on, x.days) for x in entries if x.kind == "carry_over" and x.expires_on),
        key=lambda b: b.expires_on,
    )
    used = reserved = from_entitlement = Decimal(0)
    for day in sorted(days, key=lambda x: x.leave_date):
        if day.status == "approved":
            used += HALF
        else:
            reserved += HALF
        for block in blocks:
            if day.leave_date <= block.expires_on and block.left >= HALF:
                block.left -= HALF
                break
        else:
            from_entitlement += HALF
    carried_remaining = sum((b.left for b in blocks if today <= b.expires_on), Decimal(0))
    expirable = sum((b.left for b in blocks if today > b.expires_on), Decimal(0))
    remaining = entitlement - from_entitlement
    return Balance(
        entitlement_remaining=remaining,
        carried_remaining=carried_remaining,
        used=used,
        reserved=reserved,
        unused_entitlement=max(Decimal(0), remaining),
        expirable_carried=expirable,
    )
