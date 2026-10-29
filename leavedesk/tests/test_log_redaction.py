import logging

import pytest

from app.core.logging import REDACTED, configure_logging, scrub


@pytest.fixture(autouse=True)
def _configured() -> None:
    configure_logging()


@pytest.mark.parametrize(
    ("raw", "secret"),
    [
        ("saving note=Family emergency in Da Nang", "Family"),
        ('payload {"reason": "too many people off", "id": 3}', "too many"),
        ("login password=hunter2 ok", "hunter2"),
        ("session token: abc123XYZ", "abc123XYZ"),
        ("Authorization: Bearer eyJhbGciOi", "eyJhbGciOi"),
        ("request leave_type=sick days=2", "sick"),
        ("decision_reason='not enough cover'", "not enough"),
    ],
)
def test_scrub_removes_secret_values(raw: str, secret: str) -> None:
    out = scrub(raw)
    assert secret not in out
    assert REDACTED in out


def test_scrub_keeps_harmless_text() -> None:
    assert scrub("approved request 42 for employee 7") == "approved request 42 for employee 7"


def test_log_records_are_scrubbed_with_args(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        logging.getLogger("app.test").info("cancel %s", "note=secret-note-text")
    assert "secret-note-text" not in caplog.text
    assert REDACTED in caplog.text


def test_extra_fields_with_forbidden_names_are_scrubbed(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        logging.getLogger("app.test").info("event", extra={"token": "tok-123", "request_id": "r1"})
    record = caplog.records[-1]
    assert record.token == REDACTED  # type: ignore[attr-defined]
    assert record.request_id == "r1"  # type: ignore[attr-defined]


def test_unhandled_error_log_has_no_request_secrets(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        try:
            raise RuntimeError("boom password=pw-in-exception")
        except RuntimeError:
            logging.getLogger("app.test").error("failed: %s", "password=pw-in-message")
    assert "pw-in-message" not in caplog.text
