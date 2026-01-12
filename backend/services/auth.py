from __future__ import annotations
import secrets
import uuid
from uuid import UUID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.security import verify_password
from backend.models.session import Session as DBSession
from backend.models.user import User


class InvalidCredentialsError(Exception):
    """Raised when email/password is invalid.
    Important: callers should return a generic message to avoid user enumeration.
    """


def normalize_email(email: str) -> str:
    """Normalize email for consistent lookups."""
    return email.strip().lower()


async def authenticate_local(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    """Authenticate a user using local (email + password) credentials."""
    email_norm = normalize_email(email)
    result = await session.execute(select(User).where(User.email == email_norm))
    user = result.scalar_one_or_none()

    # Avoid user enumeration: same error for "not found", "no password", "wrong password".
    if user is None or not user.hashed_password:
        raise InvalidCredentialsError

    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError

    return user


async def create_db_session(session: AsyncSession, *, user_id: UUID) -> DBSession:
    """Create and persist a server-side session row (commits immediately)."""
    db_sess = DBSession(
        id=uuid.uuid4(),
        user_id=user_id,
        csrf_secret=secrets.token_urlsafe(32),
    )
    session.add(db_sess)
    await session.commit()
    await session.refresh(db_sess)
    return db_sess


async def delete_session(session: AsyncSession, *, session_id: UUID) -> None:
    """Delete a server-side session row."""
    await session.execute(delete(DBSession).where(DBSession.id == session_id))
    await session.commit()