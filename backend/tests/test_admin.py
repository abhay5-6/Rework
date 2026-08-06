import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_admin_route_unauthorized(client: AsyncClient, test_user):
    # Login as regular user
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to access admin stats
    response = await client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "administrator privileges required" in str(response.json()).lower()

async def test_admin_route_authorized(client: AsyncClient, admin_user):
    # Login as admin user
    response = await client.post(
        "/auth/login",
        data={"username": admin_user.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Try to access admin stats
    response = await client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "users" in response.json()
