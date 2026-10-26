def test_rent_201_balance_uses_only_payments_for_that_bill(client):
    created = client.post(
        "/bills/bill-101/payments",
        json={"amount": 100_000, "idempotency_key": "rent-201-payment"},
    )
    assert created.status_code == 201
    response = client.get("/bills/bill-101")
    assert response.status_code == 200
    body = response.json()
    assert body["paid"] == 600_000
    assert body["balance"] == 900_000


def test_rent_202_payment_history_contains_only_requested_bill(client):
    response = client.get("/bills/bill-101/payments")
    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 1
    assert all(payment["bill_id"] == "bill-101" for payment in payments)


def test_rent_202_payment_history_includes_new_payments_with_amount_and_date(client):
    client.post(
        "/bills/bill-102/payments",
        json={"amount": 50_000, "idempotency_key": "rent-202-other-bill"},
    )
    created = client.post(
        "/bills/bill-101/payments",
        json={"amount": 100_000, "idempotency_key": "rent-202-payment"},
    )
    assert created.status_code == 201
    response = client.get("/bills/bill-101/payments")
    assert response.status_code == 200
    payments = response.json()
    assert [p["id"] for p in payments] == ["pay-001", created.json()["id"]]
    assert [p["amount"] for p in payments] == [500_000, 100_000]
    assert all(p["paid_at"] for p in payments)
    assert all(p["bill_id"] == "bill-101" for p in payments)


def test_rent_202_payment_history_unknown_bill_returns_404(client):
    response = client.get("/bills/bill-999/payments")
    assert response.status_code == 404


def test_rent_203_same_idempotency_key_does_not_duplicate_payment(client):
    payload = {"amount": 100_000, "idempotency_key": "request-abc"}
    first = client.post("/bills/bill-101/payments", json=payload)
    second = client.post("/bills/bill-101/payments", json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    history = client.get("/bills/bill-101/payments").json()
    assert sum(p["idempotency_key"] == "request-abc" for p in history) == 1


def test_rent_204_share_response_contains_bill_balance_and_zalo_link(client):
    response = client.get("/bills/bill-101/share")
    assert response.status_code == 200
    body = response.json()
    assert body["bill_id"] == "bill-101"
    assert "1,000,000" in body["message"] or "1000000" in body["message"]
    assert body["share_url"].startswith("https://zalo.me/")


def test_rent_205_future_due_bill_is_not_overdue(client):
    response = client.get("/bills/overdue/list")
    assert response.status_code == 200
    overdue_ids = {bill["bill_id"] for bill in response.json()}
    assert "bill-102" not in overdue_ids


def test_rent_206_bill_balance_after_payment_is_correct(client):
    before = client.get("/bills/bill-101")
    assert before.status_code == 200
    assert before.json()["balance"] == 1_000_000
    other_before = client.get("/bills/bill-102")
    assert other_before.status_code == 200
    created = client.post(
        "/bills/bill-101/payments",
        json={"amount": 100_000, "idempotency_key": "rent-206-payment"},
    )
    assert created.status_code == 201
    payment = created.json()
    assert payment["bill_id"] == "bill-101"
    assert payment["amount"] == 100_000
    after = client.get("/bills/bill-101")
    assert after.status_code == 200
    body = after.json()
    assert body["paid"] == 600_000
    assert body["balance"] == 900_000
    assert body["balance"] == body["total"] - body["paid"]
    other_after = client.get("/bills/bill-102")
    assert other_after.status_code == 200
    assert other_after.json() == other_before.json()
