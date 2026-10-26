"""Application configuration and settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Simple TODO App"
    debug: bool = False
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30

    seed_username: str = Field(min_length=3, max_length=50)
    seed_password: str = Field(min_length=8)
    seed_full_name: str = Field(min_length=1, max_length=100)

    model_config = SettingsConfigDict(
        env_prefix="APP_", env_file=".env", extra="ignore"
    )


settings = Settings()  # type: ignore[reportCallIssue]  # populated from env
