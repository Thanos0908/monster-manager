from __future__ import annotations
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.core.database import Base
from backend.utils.mixins import ReprMixin, StrMixin
from backend.enums.user_roles import UserRole

if TYPE_CHECKING:
    from backend.models.monster import Monster


class User(Base, ReprMixin, StrMixin):
    __tablename__ = "users"
    __repr_attrs__ = ("id", "email", "role")

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Identity & login
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)

    # Local login (optional if using OAuth)
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OAuth ids (optional)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    github_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    # Profile name
    name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    # Authorization 
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=False),
        index=True, nullable=False, default=UserRole.PLAYER
    )
    is_approval_pending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    monsters: Mapped[list["Monster"]] = relationship(
        back_populates="owner",
        passive_deletes=True,
    )