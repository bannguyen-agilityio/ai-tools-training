from datetime import date

from pydantic import BaseModel


class TypeBalance(BaseModel):
    leave_type: str
    entitlement: float
    carried: float
    expires_on: date | None
    carried_expired: bool
    used: float
    reserved: float
    available: float


class MyBalances(BaseModel):
    year: int
    balances: list[TypeBalance]
