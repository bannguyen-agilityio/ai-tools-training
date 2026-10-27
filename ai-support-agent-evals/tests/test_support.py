"""Deterministic behavior and privacy regression tests."""

import logging

import pytest

from src.support import answer_refund_question, log_customer_message


def test_refund_within_window_does_not_invent_guarantee() -> None:
    reply = answer_refund_question(10)
    assert reply.eligible_for_refund is True
    assert "30-day refund window" in reply.text
    assert "standard refund request process" in reply.text


def test_refund_outside_window_does_not_promise_refund() -> None:
    reply = answer_refund_question(45)
    assert reply.eligible_for_refund is False
    assert "can't promise a refund" in reply.text


def test_negative_purchase_age_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        answer_refund_question(-1)


def test_customer_message_is_not_written_to_logs(caplog: pytest.LogCaptureFixture) -> None:
    secret_text = "CUSTOMER_SECRET_123 customer@example.test"
    with caplog.at_level(logging.INFO):
        log_customer_message(secret_text)

    assert "customer_message_received" in caplog.text
    assert secret_text not in caplog.text
    assert "customer@example.test" not in caplog.text


def test_refund_response_body_is_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        reply = answer_refund_question(45)

    assert reply.text not in caplog.text
    assert "refund_question_processed" in caplog.text
