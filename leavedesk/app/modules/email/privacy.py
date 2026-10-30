"""Privacy filter for emails and notifications (R26, R35, spec §8).

The filter is structural: a RequestRef has no leave type and no note, so neither can reach a
payload. Payload keys are an allow-list, and rendered text is checked for the Sick type as a
last defence.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

# Rejection reasons go to the employee only; see build_payload.
ALLOWED_PAYLOAD_KEYS = frozenset(
    {
        "recipient_name",
        "employee_name",
        "start_date",
        "end_date",
        "link",
        "rejection_reason",
        "actor_name",
    }
)
_SICK = re.compile(r"\bsick\b", re.IGNORECASE)


class PrivacyError(ValueError):
    pass


@dataclass(frozen=True)
class RequestRef:
    """The only facts about a leave request that an email or notification may use."""

    request_id: uuid.UUID
    owner_id: uuid.UUID
    owner_name: str
    start_date: date
    end_date: date


def fmt_date(d: date) -> str:
    return f"{d:%a} {d.day} {d:%b %Y}"


def date_range(start: date, end: date) -> str:
    return fmt_date(start) if start == end else f"{fmt_date(start)} to {fmt_date(end)}"


def assert_clean(*texts: str) -> None:
    for text in texts:
        if _SICK.search(text):
            raise PrivacyError("rendered text names the Sick type")


def check_payload(payload: dict[str, Any]) -> None:
    unknown = set(payload) - ALLOWED_PAYLOAD_KEYS
    if unknown:
        raise PrivacyError(f"payload keys not in allow-list: {sorted(unknown)}")
