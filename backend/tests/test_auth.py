import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data

async def test_login_user(client: AsyncClient, test_user):
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_get_me(client: AsyncClient, test_user):
    # Login first
    login_response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    
    # Get me
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["is_system_admin"] is False
