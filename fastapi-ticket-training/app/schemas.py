from datetime import date
from pydantic import BaseModel, Field, ConfigDict


class PaymentCreate(BaseModel):
    amount: int = Field(gt=0, description="Payment amount in VND")
    idempotency_key: str = Field(min_length=1, max_length=100)


class PaymentOut(BaseModel):
    id: str
    bill_id: str
    amount: int
    paid_at: str
    idempotency_key: str


class BillOut(BaseModel):
    id: str
    tenant: str
    total: int
    paid: int
    balance: int
    due_date: date
    status: str


class ShareBillOut(BaseModel):
    bill_id: str
    tenant: str
    message: str
    share_url: str


class OverdueBillOut(BaseModel):
    bill_id: str
    tenant: str
    total: int
    balance: int
    due_date: date
    days_overdue: int
