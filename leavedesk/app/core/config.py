import os
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All deployment configuration comes from environment variables or the .env file.

    There are deliberately no defaults for deployment values: a missing variable fails
    at startup instead of silently running with a guess. The file read is chosen by
    ENV_FILE (default ".env"); real environment variables win over the file.
    """

    model_config = SettingsConfigDict(env_file=os.environ.get("ENV_FILE", ".env"), extra="ignore")

    environment: Literal["dev", "test", "staging", "production"]
    # Async SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@host:port/db
    database_url: str
    # Role the app runs as; migrations grant it table privileges.
    app_db_role: str
    # Local/CI with an owner URL: start each connection as app_db_role so the
    # restricted grants are exercised. Leave false when the URL logs in as that role.
    set_role_on_connect: bool = False
    company_tz: str
    email_backend: Literal["mock", "sendgrid"]
    # Origin used for links in emails, e.g. https://leavedesk.example.com (no trailing slash).
    app_base_url: str
    # Required when EMAIL_BACKEND=sendgrid. Held as a platform secret.
    sendgrid_api_key: str | None = None
    email_from: str | None = None
    # A-25: cookie Secure is on everywhere except plain-HTTP local dev.
    cookie_secure: bool
    # Extra origins allowed on state-changing calls (same site is always allowed).
    allowed_origins: list[str] = []
    # Session policy (R2): sliding idle window capped by an absolute maximum.
    session_idle_hours: int = 8
    session_max_hours: int = 24
    # A-6 [Assumption]: failed sign-ins allowed per IP in 15 minutes. Higher than the per-email
    # limit so the office NAT is not locked out by a few typos.
    login_ip_limit: int = 30
    # Header set by the trusted proxy with the client address (e.g. X-Forwarded-For); the
    # right-most entry is used. Unset: the socket peer address. Set it only behind a proxy.
    client_ip_header: str | None = None

    @model_validator(mode="after")
    def _no_mock_email_in_production(self) -> Settings:
        if self.environment == "production" and self.email_backend == "mock":
            raise ValueError("EMAIL_BACKEND=mock is not allowed in production")
        return self

    @model_validator(mode="after")
    def _sendgrid_needs_credentials(self) -> Settings:
        if self.email_backend == "sendgrid" and not (self.sendgrid_api_key and self.email_from):
            raise ValueError("EMAIL_BACKEND=sendgrid needs SENDGRID_API_KEY and EMAIL_FROM")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]  # values come from the environment
