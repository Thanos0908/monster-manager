import pytest


@pytest.mark.asyncio
async def test_dm_cannot_access_admin_edit_or_delete_routes(dm_client, db_session, monster_factory):
    """Authorization must be server-enforced (not only UI-hidden).
    A DM should receive a 403 Forbidden when attempting to access admin-only
    edit/delete routes.
    """

    monster_id = await monster_factory(db_session, name="Admin Only Monster", is_official=True)

    edit_resp = await dm_client.get(f"/monsters/{monster_id}/edit", follow_redirects=False)
    assert edit_resp.status_code == 403

    delete_confirm_resp = await dm_client.get(f"/monsters/{monster_id}/delete", follow_redirects=False)
    assert delete_confirm_resp.status_code == 403

    delete_post_resp = await dm_client.post(f"/monsters/{monster_id}/delete", follow_redirects=False)
    assert delete_post_resp.status_code == 403


@pytest.mark.asyncio
async def test_player_cannot_access_admin_edit_or_delete_routes(player_client, db_session, monster_factory):
    """Players must not be able to access admin-only edit/delete routes."""

    monster_id = await monster_factory(db_session, name="Admin Only Monster 2", is_official=True)

    edit_resp = await player_client.get(f"/monsters/{monster_id}/edit", follow_redirects=False)
    assert edit_resp.status_code == 403

    delete_confirm_resp = await player_client.get(f"/monsters/{monster_id}/delete", follow_redirects=False)
    assert delete_confirm_resp.status_code == 403

    delete_post_resp = await player_client.post(f"/monsters/{monster_id}/delete", follow_redirects=False)
    assert delete_post_resp.status_code == 403