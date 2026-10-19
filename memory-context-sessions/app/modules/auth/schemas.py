"""Request and response schemas for authentication."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials for logging in."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    """Data required to create a new user account."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=100)


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """Public user profile response."""

    id: int
    username: str
    full_name: str
