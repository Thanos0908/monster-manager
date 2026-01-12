import pytest

@pytest.mark.asyncio
async def test_admin_sees_edit_delete_links_on_monster_detail(admin_client, db_session, monster_factory):
    monster_id = await monster_factory(db_session, name="Detail Controls", is_official=True)

    response = await admin_client.get(f"/monsters/{monster_id}")
    assert response.status_code == 200

    assert f'href="/monsters/{monster_id}/edit"' in response.text
    assert f'href="/monsters/{monster_id}/delete"' in response.text


@pytest.mark.asyncio
async def test_player_does_not_see_edit_delete_links_on_monster_detail(player_client, db_session, monster_factory):
    monster_id = await monster_factory(db_session, name="Detail Controls 2", is_official=True)

    response = await player_client.get(f"/monsters/{monster_id}")
    assert response.status_code == 200

    assert f'href="/monsters/{monster_id}/edit"' not in response.text
    assert f'href="/monsters/{monster_id}/delete"' not in response.text