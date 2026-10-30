import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.schemas import StrictModel

MAX_DAYS = Decimal(40)
HALF = Decimal("0.5")


class EntryIn(StrictModel):
    """A manual ledger entry (R24). Opening and carry-over are 0-40; an adjustment is signed
    and bounded -40..40 [Assumption A-18]."""

    leave_type_code: Literal["annual", "sick"]
    kind: Literal["opening", "carry_over", "adjustment"]
    days: Decimal = Field(max_digits=4, decimal_places=1)  # bounded before the validator runs
    leave_year: int | None = Field(default=None, ge=2000, le=2100)
    expires_on: date | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=500)
    corrects_entry_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _rules(self) -> Self:
        if self.days % HALF != 0:
            raise ValueError("days must be in steps of 0.5")
        if self.kind == "adjustment":
            if abs(self.days) > MAX_DAYS:
                raise ValueError("days must be between -40 and 40")
            if not self.reason:
                raise ValueError("reason is required for an adjustment")
        elif not 0 <= self.days <= MAX_DAYS:
            raise ValueError("days must be between 0 and 40")
        if self.kind == "carry_over":
            if self.leave_type_code != "annual":
                raise ValueError("only Annual leave carries over")
            if self.expires_on is None:
                raise ValueError("expires_on is required for carry-over")
        elif self.expires_on is not None:
            raise ValueError("expires_on applies to carry-over only")
        if self.kind != "adjustment" and (self.reason or self.corrects_entry_id):
            raise ValueError("reason and corrects_entry_id apply to adjustments only")
        return self


class Summary(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    leave_type_code: str
    leave_year: int
    kind: str
    days: Decimal
    expires_on: date | None
    resulting_available: Decimal


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    leave_type_code: str
    leave_year: int
    kind: str
    days: Decimal
    expires_on: date | None
    reason: str | None
    source: str
    corrects_entry_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime


class BalanceOut(BaseModel):
    leave_type_code: str
    entitlement_remaining: Decimal
    carried_remaining: Decimal
    used: Decimal
    reserved: Decimal
    available: Decimal


class EmployeeBalances(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    leave_year: int
    balances: list[BalanceOut]
    ledger: list[EntryOut]


class BalanceRow(BaseModel):
    employee_id: uuid.UUID
    employee_name: str
    email: str
    balances: list[BalanceOut]


class BalanceList(BaseModel):
    leave_year: int
    items: list[BalanceRow]
