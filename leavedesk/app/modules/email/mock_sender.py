class MockEmailSender:
    """Never sends. With EMAIL_BACKEND=mock rows are stored as `mocked` and this is not called."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        raise RuntimeError("MockEmailSender must not be asked to send")
