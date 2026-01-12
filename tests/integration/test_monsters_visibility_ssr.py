import pytest

@pytest.mark.asyncio
async def test_player_sees_only_official_monsters(player_client, db_session, monster_factory):
    await monster_factory(db_session, name="Official One", is_official=True)
    await monster_factory(db_session, name="Community One", is_official=False)

    response = await player_client.get("/monsters?submitted=1", follow_redirects=False)
    assert response.status_code == 200

    assert "Official One" in response.text
    assert "Community One" not in response.text


@pytest.mark.asyncio
async def test_admin_sees_official_and_community_monsters(admin_client, db_session, monster_factory):
    await monster_factory(db_session, name="Official Two", is_official=True)
    await monster_factory(db_session, name="Community Two", is_official=False)

    response = await admin_client.get("/monsters?submitted=1", follow_redirects=False)
    assert response.status_code == 200

    assert "Official Two" in response.text
    assert "Community Two" in response.text