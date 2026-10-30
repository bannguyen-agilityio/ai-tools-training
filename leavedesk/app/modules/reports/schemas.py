import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class SummaryRow:
    employee: str
    leave_type: str
    days_taken: Decimal


@dataclass(frozen=True)
class BalanceRow:
    employee: str
    annual_available: Decimal
    annual_carried: Decimal
    sick_available: Decimal


@dataclass(frozen=True)
class OffRow:
    employee: str
    leave_type: str
    start_date: date
    end_date: date
    days_in_month: Decimal


@dataclass
class MonthlyReport:
    month: str
    summary: list[SummaryRow] = field(default_factory=list)
    balances: list[BalanceRow] = field(default_factory=list)
    off: list[OffRow] = field(default_factory=list)
    request_ids: set[uuid.UUID] = field(default_factory=set)
