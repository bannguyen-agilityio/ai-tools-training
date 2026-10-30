"""Notice rules (R14, R15; A-9). Pure: callers pass dates already in COMPANY_TZ.

Notice is the literal calendar-day difference between the start date and today. A single-day
request of a non-exempt type must start at least 1 day ahead (block). A request of more than 5
working days starting less than 7 days ahead gets a warning but may be submitted. Exempt types
(Sick) skip both.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

MIN_NOTICE_DAYS = 1
LONG_REQUEST_DAYS = Decimal(5)
LONG_NOTICE_DAYS = 7


class Notice(StrEnum):
    OK = "ok"
    BLOCK = "block"
    WARNING = "warning"


def notice_check(
    *, exempt: bool, start: date, end: date, working_days: Decimal, today: date
) -> Notice:
    if exempt:
        return Notice.OK
    lead = (start - today).days
    if start == end and lead < MIN_NOTICE_DAYS:
        return Notice.BLOCK
    if working_days > LONG_REQUEST_DAYS and lead < LONG_NOTICE_DAYS:
        return Notice.WARNING
    return Notice.OK
