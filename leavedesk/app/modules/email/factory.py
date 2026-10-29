from app.core.config import Settings, get_settings
from app.modules.email.mock_sender import MockEmailSender
from app.modules.email.sender import EmailSender
from app.modules.email.sendgrid_sender import SendGridSender


def get_sender(settings: Settings | None = None) -> EmailSender:
    settings = settings or get_settings()
    if settings.email_backend == "mock":
        return MockEmailSender()
    assert settings.sendgrid_api_key and settings.email_from  # enforced by Settings
    return SendGridSender(settings.sendgrid_api_key, settings.email_from)
