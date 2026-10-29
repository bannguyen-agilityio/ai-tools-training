from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["dev", "test", "staging", "production"] = "dev"
    database_url: str = "postgresql+psycopg://leavedesk@localhost:5432/leavedesk"
    # Role the app connects as. When set, each connection runs SET ROLE so a
    # superuser URL (local/CI) still exercises the restricted grants.
    database_role: str | None = None
    company_tz: str = "Asia/Ho_Chi_Minh"
    email_backend: Literal["mock", "sendgrid"] = "sendgrid"
    session_idle_hours: int = 8
    session_max_hours: int = 24
    # A-25: cookie Secure is on everywhere except plain-HTTP local dev.
    cookie_secure: bool = True
    # Extra origins allowed on state-changing calls (same origin is always allowed).
    allowed_origins: list[str] = []

    @model_validator(mode="after")
    def _no_mock_email_in_production(self) -> "Settings":
        if self.environment == "production" and self.email_backend == "mock":
            raise ValueError("EMAIL_BACKEND=mock is not allowed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
