import pytest

@pytest.mark.asyncio
async def test_monsters_page_does_not_render_result_links_until_search(player_client):
    response = await player_client.get("/monsters")
    assert response.status_code == 200

    # Before Search, we should not render monster detail links.
    assert 'href="/monsters/' not in response.text