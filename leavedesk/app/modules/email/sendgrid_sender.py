import httpx

from app.modules.email.sender import SendError

SEND_URL = "https://api.sendgrid.com/v3/mail/send"


class SendGridSender:
    def __init__(self, api_key: str, from_address: str) -> None:
        self._api_key = api_key
        self._from = from_address

    async def send(self, *, to: str, subject: str, body: str) -> None:
        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self._from},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    SEND_URL, json=payload, headers={"Authorization": f"Bearer {self._api_key}"}
                )
        except httpx.HTTPError as exc:
            raise SendError(None) from exc
        if response.status_code >= 300:
            raise SendError(response.status_code)
