import pytest
from urllib.parse import urlparse
import uuid


def _minimal_monster_form(*, name: str) -> dict:
    """Smallest valid Monster Create form payload.
    This project is SSR-first; the purpose of these tests is to validate the
    *end-to-end request/response cycle* (form POST -> service -> redirect ->
    detail/list visibility) without introducing browser-driven flakiness.
    """

    return {
        # Required scalars
        "name": name,
        "size": "Medium",
        "main_type": "humanoid",
        "alignment": "Neutral",
        "challenge_rating": "1",
        "armor_class_text": "10 (natural armor)",
        "hit_points": "10",
        "hit_points_dice": "3d6",
        "passive_perception": "10",

        # Required ability scores
        "ability_scores.STR": "10",
        "ability_scores.DEX": "10",
        "ability_scores.CON": "10",
        "ability_scores.INT": "10",
        "ability_scores.WIS": "10",
        "ability_scores.CHA": "10",

        # Optional JSON blocks (empty is valid)
        "traits_json": "[]",
        "actions_json": "[]",
        "reactions_json": "[]",
        "legendary_actions_json": "[]",
    }


async def _create_user_and_session_id(db_session, *, email: str, role: str) -> str:
    """Create a User + Session row and return the session_id cookie value.
    Note: We avoid using the role-specific client fixtures here because those
    fixtures share the same underlying httpx.AsyncClient instance. If multiple
    role clients are requested in the same test, their cookie values can
    overwrite each other during fixture setup.
    """

    from backend.models.user import User
    from backend.models.session import Session

    user = User(email=email, role=role)
    db_session.add(user)
    await db_session.flush()

    sess = Session(id=uuid.uuid4(), user_id=user.id, csrf_secret="test-csrf-secret")
    db_session.add(sess)
    await db_session.commit()
    return str(sess.id)


@pytest.mark.asyncio
async def test_admin_can_create_official_monster_and_player_can_view_it(client, db_session):
    """Admin POST /monsters/new should create an official monster.
    Then a PLAYER should be able to view the monster detail page (official visibility rule).
    """

    monster_name = "Admin Created Official"
    admin_session_id = await _create_user_and_session_id(
        db_session,
        email="admin@test.local",
        role="ADMIN",
    )
    player_session_id = await _create_user_and_session_id(
        db_session,
        email="player@test.local",
        role="PLAYER",
    )

    client.cookies.set("session_id", admin_session_id)
    response = await client.post(
        "/monsters/new",
        data=_minimal_monster_form(name=monster_name),
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/monsters/")
    assert "success=created" in location

    # Extract monster id from redirect URL: /monsters/<uuid>?success=created
    path = urlparse(location).path
    monster_id = path.split("/monsters/")[-1]
    assert monster_id  # sanity

    admin_detail = await client.get(f"/monsters/{monster_id}", follow_redirects=False)
    assert admin_detail.status_code == 200
    assert monster_name in admin_detail.text

    client.cookies.set("session_id", player_session_id)
    player_detail = await client.get(f"/monsters/{monster_id}", follow_redirects=False)
    assert player_detail.status_code == 200
    assert monster_name in player_detail.text


@pytest.mark.asyncio
async def test_dm_creates_pending_monster_not_visible_to_player(client, db_session):
    """DM POST /monsters/new should create a non-official (pending/community) monster.
    Players should not be able to view non-official monsters.
    """

    from sqlalchemy import select
    from backend.models.monster import Monster
    from backend.models.user import User

    dm_session_id = await _create_user_and_session_id(
        db_session,
        email="dm@test.local",
        role="DM",
    )
    player_session_id = await _create_user_and_session_id(
        db_session,
        email="player@test.local",
        role="PLAYER",
    )

    monster_name = "DM Created Pending"
    client.cookies.set("session_id", dm_session_id)
    response = await client.post(
        "/monsters/new",
        data=_minimal_monster_form(name=monster_name),
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard?success=monster_created_pending"

    # Verify DB state (connect create workflow to the official flag rule)
    dm_user = (await db_session.execute(select(User).where(User.email == "dm@test.local"))).scalar_one()
    monster = (await db_session.execute(select(Monster).where(Monster.name == monster_name))).scalar_one()

    assert monster.is_official is False
    assert monster.owner_id == dm_user.id

    # Player cannot access detail for non-official monsters
    client.cookies.set("session_id", player_session_id)
    player_detail = await client.get(f"/monsters/{monster.id}", follow_redirects=False)
    assert player_detail.status_code == 404