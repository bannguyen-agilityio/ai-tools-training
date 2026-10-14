from datetime import date
from urllib.parse import quote

from fastapi import HTTPException

from app import store


def get_bill_or_404(bill_id: str) -> dict:
    bill = store.bills.get(bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


def calculate_paid(bill_id: str) -> int:
    # SEEDED BUG (RENT-206): this sums payments for every bill,
    # rather than only payments associated with bill_id.
    return sum(payment["amount"] for payment in store.payments)


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
    # Intentionally missing bill filter (related to RENT-202).
    return list(store.payments)


def create_payment(bill_id: str, amount: int, idempotency_key: str) -> dict:
    bill = get_bill_or_404(bill_id)

    # Intentionally does not check duplicate idempotency keys (RENT-203).
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
    # The intended idempotency mapping is deliberately not updated.
    return payment


def make_share_message(bill_id: str) -> dict:
    bill = get_bill(bill_id)
    message = (
        f"Hello {bill['tenant']}, your bill {bill_id} is "
        f"{bill['balance']} VND, due {bill['due_date']}."
    )
    # Creates a URL to prefill a message. Does not actually send a message.
    return {
        "bill_id": bill_id,
        "tenant": bill["tenant"],
        "message": message,
        "share_url": f"https://zalo.me/?text={quote(message)}",
    }


def list_overdue_bills() -> list[dict]:
    today = date.today()
    result = []
    for bill in store.bills.values():
        view = get_bill(bill["id"])
        # Intentionally incomplete: any positive balance is marked overdue,
        # even when its due date is in the future (RENT-205).
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
