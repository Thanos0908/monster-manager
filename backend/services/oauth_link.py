from __future__ import annotations
from typing import Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.enums.user_roles import UserRole
from backend.models.user import User


class OAuthEmailConflictError(Exception):
    """Raised when an email is already linked to a different provider account."""


async def get_or_create_user_for_oauth(
    session: AsyncSession,
    *,
    provider: Literal["github", "google"],
    provider_id: str,
    email: str,
    name: str | None,
) -> User:
    """
    Shared OAuth user resolution rule-set:
    1) Match by provider id first (e.g. github_id == provider_id)
    2) Else match by email
       - If matched and provider field already set to a different id -> conflict
       - Else link provider id to that user
    3) Else create new user:
       - role = PLAYER
       - is_approval_pending = True
    """
    email = email.strip().lower()
    provider_id = provider_id.strip()

    if not provider_id:
        raise ValueError("provider_id cannot be empty")

    id_attr = "github_id" if provider == "github" else "google_id"

    # 1) Match by provider id
    result = await session.execute(select(User).where(getattr(User, id_attr) == provider_id))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    # 2) Match by email
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is not None:
        existing = getattr(user, id_attr)
        if existing and existing != provider_id:
            raise OAuthEmailConflictError(f"Email already linked to a different {provider} account.")

        setattr(user, id_attr, provider_id)

        # Only fill name if empty (don’t overwrite local user-chosen name)
        if user.name is None and name:
            user.name = name

        await session.commit()
        await session.refresh(user)
        return user

    # 3) Create new user
    user = User(
        email=email,
        name=name,
        role=UserRole.PLAYER,
        is_approval_pending=True,
        **{id_attr: provider_id},
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user