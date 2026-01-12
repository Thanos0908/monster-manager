import pytest


@pytest.mark.asyncio
async def test_anonymous_user_redirected_to_login(client):
    """
    Anonymous users should not access /monsters.
    They are redirected to the login page (SSR behavior).
    """
    response = await client.get("/monsters", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"