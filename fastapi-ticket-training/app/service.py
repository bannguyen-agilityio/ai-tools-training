from datetime import date

from fastapi import HTTPException

from app import store


def get_bill_or_404(bill_id: str) -> dict:
    bill = store.bills.get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


def calculate_paid(bill_id: str) -> int:
    return sum(
        payment["amount"] for payment in store.payments if payment["bill_id"] == bill_id
    )


def get_bill(bill_id: str) -> dict:
    bill = get_bill_or_404(bill_id)
    paid = calculate_paid(bill_id)
    balance = max(0, bill["total"] - paid)
    status = "paid" if balance == 0 else "unpaid"
    return {
        "id": bill["id"],
        "tenant": bill["tenant"],
        "total": bill["total"],
        "paid": paid,
        "balance": balance,
        "due_date": bill["due_date"],
        "status": status,
    }


def list_payments(bill_id: str) -> list[dict]:
    get_bill_or_404(bill_id)
    return list(store.payments)


def create_payment(bill_id: str, amount: int, idempotency_key: str) -> dict:
    bill = get_bill_or_404(bill_id)

    current = get_bill(bill_id)
    if amount > current["balance"]:
        raise HTTPException(status_code=400, detail="Payment exceeds outstanding balance")

    payment = {
        "id": f"pay-{len(store.payments) + 1:03d}",
        "bill_id": bill["id"],
        "amount": amount,
        "paid_at": date.today().isoformat(),
        "idempotency_key": idempotency_key,
    }
    store.payments.append(payment)
    return payment


def list_overdue_bills() -> list[dict]:
    today = date.today()
    result = []
    for bill in store.bills.values():
        view = get_bill(bill["id"])
        if view["balance"] > 0:
            days_overdue = max(0, (today - bill["due_date"]).days)
            result.append({
                "bill_id": bill["id"],
                "tenant": bill["tenant"],
                "total": bill["total"],
                "balance": view["balance"],
                "due_date": bill["due_date"],
                "days_overdue": days_overdue,
            })
    return result
