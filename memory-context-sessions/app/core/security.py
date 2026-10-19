"""Password hashing and JWT token utilities."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings

PASSWORD_ITERATIONS = 100_000
_ALGORITHM = "HS256"


def hash_password(password: str, salt: str) -> str:
    """Hash a password with the given salt using PBKDF2-SHA256.

    Args:
        password: The plaintext password.
        salt: The salt for hashing.

    Returns:
        The hex-encoded password hash.
    """
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS
    )
    return digest.hex()


def verify_password(plain: str, salt: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        plain: The plaintext password to verify.
        salt: The salt used when the password was hashed.
        hashed: The stored password hash.

    Returns:
        True if the password matches.
    """
    return hmac.compare_digest(hash_password(plain, salt), hashed)


def generate_salt() -> str:
    """Generate a cryptographically secure random salt."""
    import secrets

    return secrets.token_hex(16)


def create_access_token(username: str) -> str:
    """Create a signed JWT access token for the given username.

    Args:
        username: The subject of the token.

    Returns:
        An encoded JWT string.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode a JWT access token and return the username.

    Args:
        token: The encoded JWT string.

    Returns:
        The username, or None if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
