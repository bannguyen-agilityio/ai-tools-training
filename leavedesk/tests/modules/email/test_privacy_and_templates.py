import uuid
from datetime import date

import pytest

from app.modules.email import privacy
from app.modules.email.templates import Event, render

REF = privacy.RequestRef(
    uuid.uuid4(), uuid.uuid4(), "Anna Le", date(2026, 11, 2), date(2026, 11, 4)
)
PAYLOAD = {
    "recipient_name": "Binh",
    "employee_name": REF.owner_name,
    "dates": privacy.date_range(REF.start_date, REF.end_date),
    "link": "http://x/requests/1",
}


# R26 privacy: property-style over every template
@pytest.mark.parametrize("event", list(Event))
def test_no_template_names_sick_or_a_note(event: Event) -> None:
    out = render(event, PAYLOAD)
    for text in (out.subject, out.body, out.notification_title or "", out.notification_body or ""):
        assert not privacy._SICK.search(text)
        assert "note" not in text.lower()
        assert "Reason" not in text  # only present when a reason is supplied
    assert PAYLOAD["link"] in out.body


@pytest.mark.parametrize("event", [Event.INVITE, Event.PASSWORD_RESET])
def test_invite_and_reset_are_email_only(event: Event) -> None:
    assert render(event, PAYLOAD).notification_title is None


def test_rejection_reason_in_email_but_never_in_notification() -> None:
    out = render(Event.REQUEST_REJECTED, {**PAYLOAD, "rejection_reason": "Team is short"})
    assert "Team is short" in out.body
    assert "Team is short" not in (out.notification_body or "")


def test_dates_are_unambiguous() -> None:
    assert PAYLOAD["dates"] == "Mon 2 Nov 2026 to Wed 4 Nov 2026"


def test_payload_allow_list_and_sick_guard() -> None:
    with pytest.raises(privacy.PrivacyError):
        privacy.check_payload({"leave_type": "sick"})
    with pytest.raises(privacy.PrivacyError):
        privacy.assert_clean("Your Sick leave")
    privacy.assert_clean("Sickles Office")
