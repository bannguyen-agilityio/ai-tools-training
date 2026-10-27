"""Minimal support policy example used by the evaluation project."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

REFUND_WINDOW_DAYS = 30


@dataclass(frozen=True)
class SupportReply:
    text: str
    eligible_for_refund: bool | None


def answer_refund_question(days_since_purchase: int) -> SupportReply:
    """Answer a refund eligibility question using the approved sample policy.

    Sample policy: purchases are eligible for a refund within 30 days.
    Outside that window, the response does not promise a refund.
    """
    if days_since_purchase < 0:
        raise ValueError("days_since_purchase cannot be negative")

    if days_since_purchase <= REFUND_WINDOW_DAYS:
        message = (
            f"Your purchase is within the {REFUND_WINDOW_DAYS}-day refund "
            "window. Please follow the standard refund request process."
        )
        eligible: bool | None = True
    else:
        message = (
            f"Your purchase is outside the {REFUND_WINDOW_DAYS}-day refund "
            "window. I can't promise a refund; please contact support for review."
        )
        eligible = False

    # Log only a fixed event label, never customer input or response text.
    logger.info("refund_question_processed")
    return SupportReply(text=message, eligible_for_refund=eligible)


def log_customer_message(message: str) -> None:
    """Record that a message was received without logging its contents."""
    # Avoid logging message itself, its length, or any derived personal data.
    del message
    logger.info("customer_message_received")
