from __future__ import annotations
from typing import Callable, Literal, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_session
from backend.models.monster import Monster
from backend.models.user import User
from backend.models.session import Session as DBSession

SESSION_COOKIE_NAME = "session_id"

# Authorization layer uses normalized lowercase role strings 
# ('admin'/'dm'/'player') for consistent comparisons.
Role = Literal["admin", "dm", "player"] 


def _safe_role_str(user: User) -> Role: 
    """Normalize a user role to a lowercase string literal."""
    raw = getattr(user.role, "value", user.role)
    return str(raw).lower()


async def get_current_session(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Optional[DBSession]:
    """
    Load the current DB session from the cookie.
    Returns None if unauthenticated or cookie invalid.
    """
    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if not sid:
        return None

    try:
        session_id = UUID(sid)
    except ValueError:
        return None

    result = await session.execute(select(DBSession).where(DBSession.id == session_id))
    return result.scalar_one_or_none()


async def get_current_user(
    db_sess: Optional[DBSession] = Depends(get_current_session),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Resolve the logged-in User from the DB session.
    Returns None if anonymous or user missing.
    """
    if not db_sess:
        return None

    result = await session.execute(select(User).where(User.id == db_sess.user_id))
    return result.scalar_one_or_none()

async def get_optional_current_user(
    user: Optional[User] = Depends(get_current_user),
) -> Optional[User]:
    """FastAPI dependency that resolves the current user if authenticated,
    or returns None for anonymous requests without raising errors."""
    return user


async def require_authenticated(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_role(*allowed: Role) -> Callable[[Optional[User]], User]:
    """
    Dependency factory: ensure current user's role is in `allowed` roles.
    """
    allowed_set = set(allowed)

    async def _dep(user: Optional[User] = Depends(require_authenticated)) -> User:
        role_lc = _safe_role_str(user)
        if role_lc not in allowed_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


admin_only = require_role("admin")
dm_or_admin = require_role("admin", "dm")
player_or_better = require_role("admin", "dm", "player")


async def get_current_role(user: Optional[User] = Depends(get_current_user)) -> Optional[Role]:
    """Return just the role string if present."""
    if not user:
        return None
    return _safe_role_str(user)


def monster_filter_admin_no_filter():
    """
    For Admins: no restriction on visibility.
    Usage: .where(monster_filter_admin_no_filter())
    """
    return true()  # SELECT ... WHERE TRUE  (no-op filter)


def monster_filter_official_only():
    """
    For DMs/Players/Anonymous: only official monsters are visible.
    Usage: .where(monster_filter_official_only())
    """
    return Monster.is_official.is_(True)


def monster_filter_for_user(user: User | None):
    """
    Return the appropriate SQLAlchemy visibility filter for a given user.
    Rules:
    - Admins can see all monsters (no filter).
    - Non-admins and anonymous users can only see official monsters.
    """
    role = _safe_role_str(user) if user else "player"
    return monster_filter_admin_no_filter() if role == "admin" else monster_filter_official_only()


def enforce_monster_official_flag_on_save(actor: User, monster: Monster) -> None:
    """
    Central rule you defined:
      - Admin writes => monster.is_official = True
      - DM writes    => monster.is_official = False
      - Player does not write (It is enforced elsewhere)
    Called in the service just before commit/flush.
    """
    role = _safe_role_str(actor)
    if role == "admin":
        monster.is_official = True
    else:
        monster.is_official = False