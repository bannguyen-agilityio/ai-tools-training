from typing import Protocol


class SendError(Exception):
    """A delivery attempt failed. `code` is the provider status code, or None for network errors.

    Carries no message text: provider responses can echo the mail content.
    """

    def __init__(self, code: int | None) -> None:
        super().__init__(f"send failed: {code}")
        self.code = code


class EmailSender(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None:
        """Deliver one plain-text mail or raise SendError."""
        ...
