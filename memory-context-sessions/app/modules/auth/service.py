"""Business logic for authentication."""

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_salt,
    hash_password,
    verify_password,
)
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository


class AuthService:
    """Handle authentication use cases."""

    def __init__(self, user_repo: UserRepository) -> None:
        """Initialize the service.

        Args:
            user_repo: The user data-access repository.
        """
        self._user_repo = user_repo

    async def register(self, username: str, password: str, full_name: str) -> User:
        """Create a new user account.

        Args:
            username: The desired username.
            password: The plaintext password.
            full_name: The user's display name.

        Returns:
            The newly created user.

        Raises:
            ConflictError: If the username is already taken.
        """
        existing = await self._user_repo.get_by_username(username)
        if existing:
            raise ConflictError(
                message="Username already exists",
                code="USERNAME_ALREADY_EXISTS",
            )
        salt = generate_salt()
        user = User(
            username=username,
            password_hash=hash_password(password, salt),
            salt=salt,
            full_name=full_name,
        )
        return await self._user_repo.create(user)

    async def authenticate(self, username: str, password: str) -> str:
        """Verify credentials and return a JWT access token.

        Args:
            username: The username to authenticate.
            password: The plaintext password.

        Returns:
            A signed JWT access token.

        Raises:
            AuthenticationError: If the credentials are invalid.
        """
        user = await self._user_repo.get_by_username(username)
        if not user or not verify_password(password, user.salt, user.password_hash):
            raise AuthenticationError(
                message="Incorrect username or password",
                code="INVALID_CREDENTIALS",
            )
        return create_access_token(user.username)

    def resolve_token(self, token: str) -> str:
        """Decode a JWT and return the username.

        Args:
            token: The JWT access token.

        Returns:
            The username.

        Raises:
            AuthenticationError: If the token is invalid or expired.
        """
        username = decode_access_token(token)
        if not username:
            raise AuthenticationError(
                message="Invalid or expired token",
                code="INVALID_TOKEN",
            )
        return username

    async def get_user(self, username: str) -> User | None:
        """Return the user record for the given username.

        Args:
            username: The username to look up.

        Returns:
            The user record, or None if not found.
        """
        return await self._user_repo.get_by_username(username)
