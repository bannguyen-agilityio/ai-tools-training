from fastapi import FastAPI

from app.schemas import BillOut, OverdueBillOut, PaymentCreate, PaymentOut
from app.service import create_payment, get_bill, list_overdue_bills, list_payments

app = FastAPI(title="Room Rental Billing API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/bills/{bill_id}", response_model=BillOut)
def read_bill(bill_id: str):
    return get_bill(bill_id)


@app.get("/bills/{bill_id}/payments", response_model=list[PaymentOut])
def read_payments(bill_id: str):
    return list_payments(bill_id)


@app.post("/bills/{bill_id}/payments", response_model=PaymentOut, status_code=201)
def add_payment(bill_id: str, payload: PaymentCreate):
    return create_payment(bill_id, payload.amount, payload.idempotency_key)


@app.get("/bills/overdue/list", response_model=list[OverdueBillOut])
def overdue_bills():
    return list_overdue_bills()
