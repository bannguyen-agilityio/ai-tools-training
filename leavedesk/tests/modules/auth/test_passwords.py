import pytest

from app.modules.auth.passwords import PasswordPolicyError, hash_password, validate_password


@pytest.mark.parametrize(
    "pw", ["short-11-ch", "password1234", "Password123456", "qwertyuiop12", "aaaaaaaaaaaa"]
)
def test_rejected(pw: str):
    with pytest.raises(PasswordPolicyError):
        validate_password(pw)


def test_accepted_and_hash_is_argon2id():
    validate_password("correct horse battery")
    assert hash_password("correct horse battery").startswith("$argon2id$")
