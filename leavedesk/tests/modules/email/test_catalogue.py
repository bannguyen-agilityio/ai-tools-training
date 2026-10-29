"""Event catalogue conformance (R26).

Templates for all eight events exist. Call sites for request events ship with the plan that
creates each event; each of those plans removes its event from PENDING_WIRING, and the last
one to merge deletes the set.
"""

from app.modules.email.templates import Event

WIRED = {Event.INVITE, Event.PASSWORD_RESET}  # wired by plan 04 (identity)
PENDING_WIRING = {
    Event.REQUEST_CREATED,  # plan 10
    Event.REQUEST_APPROVED,  # plan 13
    Event.REQUEST_REJECTED,  # plan 13
    Event.REQUEST_CANCELLED_BY_EMPLOYEE,  # plan 12
    Event.REQUEST_CANCELLED_BY_HR,  # plan 14
    Event.REQUEST_APPROVED_ON_BEHALF,  # plan 15/16
}


def test_every_event_is_wired_or_pending() -> None:
    assert WIRED | PENDING_WIRING == set(Event)
    assert not WIRED & PENDING_WIRING


def test_eight_events() -> None:
    assert len(Event) == 8
