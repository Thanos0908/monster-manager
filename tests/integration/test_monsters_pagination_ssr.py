import pytest

@pytest.mark.asyncio
async def test_monsters_page_clamps_high_page_number(admin_client, db_session, monster_factory):
    # Arrange: create 30 monsters so we have >1 page (page size is 25)
    for i in range(30):
        await monster_factory(db_session, name=f"Monster {i:02d}", is_official=True)

    # Act: request an absurdly high page
    response = await admin_client.get("/monsters?submitted=1&page=999", follow_redirects=False)
    assert response.status_code == 200

    # Assert: page should still render results (not crash, not empty weirdness)
    assert 'href="/monsters/' in response.text