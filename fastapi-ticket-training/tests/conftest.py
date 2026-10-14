import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import store


@pytest.fixture(autouse=True)
def reset_store():
    store.bills["bill-101"]["total"] = 1_500_000
    store.bills["bill-102"]["total"] = 900_000
    store.bills["bill-103"]["total"] = 700_000
    store.payments[:] = [
        {"id": "pay-001", "bill_id": "bill-101", "amount": 500_000, "paid_at": "2026-10-01", "idempotency_key": "seed-101"},
        {"id": "pay-002", "bill_id": "bill-102", "amount": 200_000, "paid_at": "2026-10-02", "idempotency_key": "seed-102"},
    ]
    store.idempotency_keys.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)
