import pytest

@pytest.mark.asyncio
async def test_admin_can_load_delete_confirm_page(admin_client, db_session, monster_factory):
    monster_id = await monster_factory(db_session, name="To Delete", is_official=True)

    response = await admin_client.get(f"/monsters/{monster_id}/delete", follow_redirects=False)
    assert response.status_code == 200

    # Confirm page should reference the monster name
    assert "To Delete" in response.text


@pytest.mark.asyncio
async def test_player_cannot_load_delete_confirm_page(player_client, db_session, monster_factory):
    monster_id = await monster_factory(db_session, name="To Delete 2", is_official=True)

    response = await player_client.get(f"/monsters/{monster_id}/delete", follow_redirects=False)

    # depending on your auth policy this might be 403 or 303 -> /login
    assert response.status_code in (403, 303)