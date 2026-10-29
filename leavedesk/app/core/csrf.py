import hashlib
import hmac
import secrets
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.errors import problem

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_HEADER = "X-CSRF-Token"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(presented: str | None, stored_hash: str) -> bool:
    return bool(presented) and hmac.compare_digest(hash_token(presented or ""), stored_hash)


class OriginCheckMiddleware(BaseHTTPMiddleware):
    """Refuse state-changing calls whose Origin is not this site (R29c).

    The X-CSRF-Token check needs the session, so it lives in get_current_user.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in SAFE_METHODS:
            origin = request.headers.get("origin")
            if origin is not None:
                # Compare host[:port] with the Host header, not the scheme: TLS is
                # terminated by the platform proxy, so request.url may say http.
                same_site = urlsplit(origin).netloc == request.headers.get("host")
                if not same_site and origin.rstrip("/") not in get_settings().allowed_origins:
                    return problem(403, "Cross-origin request refused")
        return await call_next(request)
