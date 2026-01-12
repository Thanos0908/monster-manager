"""Security utilities.
This project uses server-side sessions stored in Postgres.
For local auth, we only need password hashing + verification.
"""
from __future__ import annotations
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using the configured password context."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored password hash."""
    return pwd_context.verify(plain_password, hashed_password)
