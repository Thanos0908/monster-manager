import pytest

@pytest.mark.asyncio
async def test_player_can_access_monsters_page(player_client):
    response = await player_client.get("/monsters")
    assert response.status_code == 200