"""SQLAlchemy model for server-side login sessions stored in the database."""

from __future__ import annotations
import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.user import User

class Session(Base, ReprMixin):
    """
    Server-side login session stored in the database.
    Flow:
    - On login, the server creates a session row (id, user_id, csrf_secret).
    - The response sets a cookie: session_id=<UUID>.
    - Each request resolves the current user by looking up that session id.
    - On logout, the session row is deleted, invalidating the cookie immediately.
    """
    __tablename__ = "sessions"
    __repr_attrs__ = ("id", "user_id")

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    user: Mapped["User"] = relationship("User")
    
    csrf_secret: Mapped[str] = mapped_column(String(128), nullable=False)