"""Application configuration and settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Simple TODO App"
    debug: bool = False
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30

    model_config = {"env_prefix": "APP_", "env_file": ".env"}


settings = Settings()  # type: ignore[reportCallIssue]  # populated from env
