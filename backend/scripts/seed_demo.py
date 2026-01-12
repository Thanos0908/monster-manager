"""
Seed demo data for local development / portfolio review.
Creates (or updates) three users:
- admin@example.com  (ADMIN)
- dm@example.com     (DM)
- player@example.com (PLAYER)
Idempotent:
- Re-running will NOT create duplicates.
- Users are matched by email.
Run (recommended):
    python -m backend.scripts.seed_demo
Alternative:
    python backend/scripts/seed_demo.py
Safety:
- Set ALLOW_SEED_DEMO=1 to run.
"""

from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Allow running as a plain script from project root or anywhere.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.database import get_session_factory  # noqa: E402
from backend.core.security import hash_password  # noqa: E402
from backend.enums.user_roles import UserRole  # noqa: E402
from backend.models.user import User  # noqa: E402


DEMO_PASSWORD = "demo-password-123"
RESET_PASSWORDS = os.getenv("RESET_DEMO_PASSWORDS", "0") == "1"


DEMO_USERS = [
    {"email": "admin@example.com", "role": UserRole.ADMIN, "name": "Demo Admin"},
    {"email": "dm@example.com", "role": UserRole.DM, "name": "Demo DM"},
    {"email": "player@example.com", "role": UserRole.PLAYER, "name": "Demo Player"},
]


async def upsert_user(session: AsyncSession, *, email: str, role: UserRole, name: str) -> User:
    email_norm = email.strip().lower()

    result = await session.execute(select(User).where(User.email == email_norm))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email_norm,
            name=name,
            role=role,
            is_approval_pending=False,
            hashed_password=hash_password(DEMO_PASSWORD),
        )
        session.add(user)
        await session.flush()
        print(f"Created user: {email_norm} ({role.value})")
        return user

    # Update only what we actually want to enforce.
    changed = False

    if user.role != role:
        user.role = role
        changed = True

    if user.is_approval_pending:
        user.is_approval_pending = False
        changed = True

    if user.name != name:
        user.name = name
        changed = True

    if RESET_PASSWORDS:
        user.hashed_password = hash_password(DEMO_PASSWORD)
        changed = True

    if changed:
        msg = "Updated user" if not RESET_PASSWORDS else "Updated user (and reset demo password)"
        print(f"{msg}: {email_norm} ({role.value})")
    else:
        print(f"User already OK: {email_norm} ({role.value})")

    return user


async def seed_demo() -> None:
    if os.getenv("ALLOW_SEED_DEMO") != "1":
        raise RuntimeError("Refusing to run: set ALLOW_SEED_DEMO=1 to seed demo data.")

    session_factory = get_session_factory()

    async with session_factory() as session:
        for u in DEMO_USERS:
            await upsert_user(session, email=u["email"], role=u["role"], name=u["name"])

        await session.commit()

    print("\nDone.")
    print("Demo accounts:")
    print(" - admin@example.com")
    print(" - dm@example.com")
    print(" - player@example.com")
    print(f"Password for all: {DEMO_PASSWORD}")
    if not RESET_PASSWORDS:
        print("(Tip: set RESET_DEMO_PASSWORDS=1 to reset passwords on re-run.)")


def main() -> None:
    asyncio.run(seed_demo())


if __name__ == "__main__":
    main()