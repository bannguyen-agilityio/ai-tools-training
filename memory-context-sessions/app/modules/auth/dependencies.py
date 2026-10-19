"""Dependency injection for the auth module."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db_session
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService

bearer_scheme = HTTPBearer()


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    """Provide a user repository backed by the request database session."""
    return UserRepository(session)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    """Provide the auth service with its repository dependency."""
    return AuthService(user_repo)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> str:
    """Resolve the current user from the bearer token.

    Args:
        credentials: The HTTP bearer credentials.
        auth_service: The authentication service.

    Returns:
        The authenticated username.

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    return auth_service.resolve_token(credentials.credentials)
