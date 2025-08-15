import asyncio
from backend.core.database import get_session_factory
from backend.models.user import User, UserRole
import uuid

async def main():
    session_factory = get_session_factory()

    async with session_factory() as session:
        # Create a new user
        new_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password="fakehashed",  # we'll hash later
            role=UserRole.PLAYER,
            is_approval_pending=True
        )
        session.add(new_user)
        await session.commit()
        print(f"✅ Created user: {new_user.username}")

if __name__ == "__main__":
    asyncio.run(main())