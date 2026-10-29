"""Password policy and Argon2id hashing (R2). argon2-cffi's default PasswordHasher is Argon2id."""

import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

MIN_LENGTH = 12

_hasher = PasswordHasher()

# [Assumption] A short built-in list of the most common passwords (public knowledge, no licence
# issue). Candidates are lowercased and stripped of trailing digits/punctuation before the check.
COMMON = frozenset(
    """
    password passw0rd p@ssw0rd p@ssword letmein welcome admin administrator qwerty qwertyuiop
    qwertyuiopasdfghjkl asdfghjkl zxcvbnm iloveyou monkey dragon master sunshine princess football
    baseball superman batman trustno1 abc abcdef abcdefgh abcdefghijkl abcdefghijklmnop
    changeme default secret login whatever freedom shadow michael jennifer starwars hello helloworld
    asnet asnetvn leavedesk leave company companyname vietnam hanoi saigon hochiminh
    iloveyou1 welcome1 letmein1 monkey123 dragon123 passwordpassword
    """.split()
)
_TRAILING = re.compile(r"[\d\W_]+$")


class PasswordPolicyError(ValueError):
    pass


def validate_password(password: str) -> None:
    if len(password) < MIN_LENGTH:
        raise PasswordPolicyError(f"Password must be at least {MIN_LENGTH} characters.")
    lowered = password.lower()
    stripped = _TRAILING.sub("", lowered)
    if lowered in COMMON or stripped in COMMON or len(set(lowered)) < 4:
        raise PasswordPolicyError("That password is too common. Choose a different one.")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError, InvalidHashError:
        return False


def needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


# Verified against for unknown emails so both paths cost one Argon2 verification (R1).
DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation")
