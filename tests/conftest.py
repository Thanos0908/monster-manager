import os
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
# Import app after we set env / clear caches in fixtures when needed
from backend.app import app
from decimal import Decimal


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    Read TEST_DATABASE_URL from .env / environment.
    We keep it explicit so tests never accidentally use the dev DATABASE_URL.
    """
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL is not set. Add it to your .env, e.g. "
            "TEST_DATABASE_URL=postgresql+asyncpg://monster_user:password@localhost:5432/monsters_test"
        )
    return url


@pytest.fixture
def engine(test_database_url: str) -> AsyncEngine:
    """
    Create a fresh async engine per test.
    This avoids "Event loop is closed" issues on Windows because asyncpg
    connections/pools are bound to the event loop they were created on.
    """
    return create_async_engine(test_database_url, future=True)


@pytest.fixture(autouse=True)
async def dispose_engine_after_test(engine: AsyncEngine):
    yield
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
async def reset_schema(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """
    Reset schema before each test: drop all tables and recreate them.
    This is the simplest reliable strategy because services commit().
    It runs ONLY against the test DB.
    """
    # Import Base lazily so model metadata is loaded.
    from backend.core.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield


@pytest.fixture
async def db_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """
    Direct DB session fixture for service-layer tests.
    """
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP client for integration tests.
    Overrides the app's DB dependency to use the test session factory.
    """
    from backend.core.database import get_session
    from httpx import ASGITransport

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    

@pytest.fixture
def monster_factory():
    async def _create_monster(
        db: AsyncSession,
        *,
        name: str,
        is_official: bool,
    ) -> str:
        from backend.models.monster import Monster

        monster = Monster(
            name=name,
            is_official=is_official,

            challenge_rating=Decimal("1.000"),
            armor_class_text="10 (natural armor)",
            passive_perception=10,

            size="Medium",
            main_type="humanoid",
            alignment="neutral",

            hit_points=10,
            hit_points_dice="3d6",

            str_score=10,
            dex_score=10,
            con_score=10,
            int_score=10,
            wis_score=10,
            cha_score=10,
        )

        db.add(monster)
        await db.commit()
        await db.refresh(monster)
        return str(monster.id)

    return _create_monster


async def _create_user_and_session(
    db: AsyncSession,
    *,
    email: str,
    role: str,
) -> str:
    """
    Helper that inserts a User + Session and returns the session_id cookie value.
    Adjust imports/model fields if your names differ.
    """
    from backend.models.user import User
    from backend.models.session import Session

    user = User(email=email, role=role)
    db.add(user)
    await db.flush()  # gets user.id without committing

    session = Session(user_id=user.id, csrf_secret="test-csrf-secret")
    db.add(session)
    await db.commit()

    return str(session.id)


@pytest.fixture
async def admin_client(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    session_id = await _create_user_and_session(db_session, email="admin@test.local", role="ADMIN")
    client.cookies.set("session_id", session_id)
    yield client


@pytest.fixture
async def dm_client(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    session_id = await _create_user_and_session(db_session, email="dm@test.local", role="DM")
    client.cookies.set("session_id", session_id)
    yield client


@pytest.fixture
async def player_client(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    session_id = await _create_user_and_session(db_session, email="player@test.local", role="PLAYER")
    client.cookies.set("session_id", session_id)
    yield client