from datetime import date, timedelta

# In-memory fixtures. Restarting the app resets this data.
bills = {
    "bill-101": {
        "id": "bill-101",
        "tenant": "Lan",
        "total": 1_500_000,
        "due_date": date.today() - timedelta(days=3),
    },
    "bill-102": {
        "id": "bill-102",
        "tenant": "Minh",
        "total": 900_000,
        "due_date": date.today() + timedelta(days=5),
    },
    "bill-103": {
        "id": "bill-103",
        "tenant": "An",
        "total": 700_000,
        "due_date": date.today() - timedelta(days=2),
    },
}

payments = [
    {
        "id": "pay-001",
        "bill_id": "bill-101",
        "amount": 500_000,
        "paid_at": "2026-10-01",
        "idempotency_key": "seed-101",
    },
    {
        "id": "pay-002",
        "bill_id": "bill-102",
        "amount": 200_000,
        "paid_at": "2026-10-02",
        "idempotency_key": "seed-102",
    },
]

# Used to prevent replaying a request.
idempotency_keys: dict[str, str] = {}
