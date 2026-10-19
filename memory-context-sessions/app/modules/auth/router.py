"""HTTP endpoints for authentication."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.exceptions import NotFoundError
from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.schemas import LoginRequest, RegisterRequest, Token, UserOut
from app.modules.auth.service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserOut:
    """Create a new user account.

    Args:
        body: The registration data.
        auth_service: The authentication service.

    Returns:
        The newly created user's public profile.

    Raises:
        ConflictError: If the username is already taken.
    """
    user = await auth_service.register(body.username, body.password, body.full_name)
    return UserOut(id=user.id, username=user.username, full_name=user.full_name)


@router.post("/login", response_model=Token)
async def login(
    body: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    """Authenticate with username and password to receive an access token.

    Args:
        body: The login credentials.
        auth_service: The authentication service.

    Returns:
        An access token.

    Raises:
        AuthenticationError: If credentials are invalid.
    """
    token = await auth_service.authenticate(body.username, body.password)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def read_current_user(
    username: Annotated[str, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserOut:
    """Return the profile of the currently authenticated user.

    Args:
        username: The current user's username.
        auth_service: The authentication service.

    Returns:
        The user's public profile.
    """
    user = await auth_service.get_user(username)
    if not user:
        raise NotFoundError(message="User not found", code="USER_NOT_FOUND")
    return UserOut(id=user.id, username=user.username, full_name=user.full_name)
