import uuid

from pydantic import BaseModel, Field

from app.core.schemas import StrictModel

# Upper bound keeps Argon2 work and request size sane; the minimum is enforced by the policy.
Password = Field(max_length=256)


class LoginIn(StrictModel):
    email: str = Field(max_length=254)
    password: str = Password


class TokenPasswordIn(StrictModel):
    token: str = Field(min_length=1, max_length=200)
    password: str = Password


class ResetRequestIn(StrictModel):
    email: str = Field(max_length=254)


class PasswordChangeIn(StrictModel):
    current_password: str = Password
    new_password: str = Password


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str


class MeOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    is_hr_deputy: bool
    team: TeamOut | None
    csrf_token: str
    api_version: str = "v1"
