"""Event catalogue and templates (R26).

Every email says "leave", never the type. Request-event templates are defined here; the call
sites ship with the plan that creates each event (see tests/modules/email/test_catalogue.py).
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Event(StrEnum):
    REQUEST_CREATED = "request_created"
    REQUEST_APPROVED = "request_approved"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_CANCELLED_BY_EMPLOYEE = "request_cancelled_by_employee"
    REQUEST_CANCELLED_BY_HR = "request_cancelled_by_hr"
    REQUEST_APPROVED_ON_BEHALF = "request_approved_on_behalf"
    REQUEST_REJECTED_ON_BEHALF = "request_rejected_on_behalf"
    INVITE = "invite"
    PASSWORD_RESET = "password_reset"


@dataclass(frozen=True)
class Rendered:
    subject: str
    body: str
    # None: email only (the invitee cannot sign in yet, R35).
    notification_title: str | None
    notification_body: str | None


def _closing(link: str) -> str:
    return f"\nOpen it here: {link}\n"


def _request(event: Event, p: dict[str, Any]) -> Rendered:
    who, when, link = p["employee_name"], p["dates"], p["link"]
    match event:
        case Event.REQUEST_CREATED:
            line = f"{who} requested leave for {when}."
            subject = "Leave request awaiting your decision"
        case Event.REQUEST_APPROVED:
            line = f"Your leave for {when} was approved."
            subject = "Your leave request was approved"
        case Event.REQUEST_REJECTED:
            line = f"Your leave for {when} was rejected."
            subject = "Your leave request was rejected"
        case Event.REQUEST_CANCELLED_BY_EMPLOYEE:
            line = f"{who} cancelled their leave for {when}."
            subject = "Leave request cancelled"
        case Event.REQUEST_CANCELLED_BY_HR:
            line = f"HR cancelled the leave for {when}."
            subject = "Leave cancelled by HR"
        case Event.REQUEST_APPROVED_ON_BEHALF:
            line = f"{p['actor_name']} approved the leave of {who} for {when} on your behalf."
            subject = "Leave approved on your behalf"
        case _:
            line = f"{p['actor_name']} rejected the leave of {who} for {when} on your behalf."
            subject = "Leave rejected on your behalf"
    body = f"Hello {p['recipient_name']},\n\n{line}"
    if event is Event.REQUEST_REJECTED and p.get("rejection_reason"):
        body += f"\nReason: {p['rejection_reason']}"
    return Rendered(subject, body + "\n" + _closing(link), subject, line)


def render(event: Event, payload: dict[str, Any]) -> Rendered:
    """`payload` holds the allow-listed fields plus `dates` (formatted by the caller)."""
    if event is Event.INVITE:
        return Rendered(
            "Your LeaveDesk invitation",
            f"Hello {payload['recipient_name']},\n\nYou have been invited to LeaveDesk. "
            f"Set your password to get started.{_closing(payload['link'])}",
            None,
            None,
        )
    if event is Event.PASSWORD_RESET:
        return Rendered(
            "Reset your LeaveDesk password",
            f"Hello {payload['recipient_name']},\n\nUse this link to reset your password. "
            f"If you did not ask for it, ignore this email.{_closing(payload['link'])}",
            None,
            None,
        )
    return _request(event, payload)
