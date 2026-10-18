"""Password hashing and verification using Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type


_MAX_PASSWORD_BYTES = 1024

_PASSWORD_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19 * 1024,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    encoded = password.encode("utf-8")
    if not encoded:
        raise ValueError("password must not be empty")
    if len(encoded) > _MAX_PASSWORD_BYTES:
        raise ValueError("password is too long")
    return encoded


def hash_password(password: str) -> str:
    """Return a versioned, salted password hash suitable for storage."""

    _password_bytes(password)
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password without revealing why authentication failed."""

    try:
        _password_bytes(password)
        return _PASSWORD_HASHER.verify(stored_hash, password)
    except (TypeError, ValueError, VerificationError, VerifyMismatchError, InvalidHashError):
        return False

