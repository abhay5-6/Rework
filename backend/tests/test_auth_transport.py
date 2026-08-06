import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.membership import WorkspaceMembership
from app.core.security import hash_password, create_websocket_ticket, decode_websocket_ticket, TokenDecodeError

pytestmark = pytest.mark.asyncio


async def _create_test_user(db: AsyncSession, prefix: str = "authtransport") -> User:
    uid = str(uuid.uuid4())[:8]
    user = User(
        username=f"{prefix}_{uid}",
        email=f"{prefix}_{uid}@example.com",
        hashed_password=hash_password("Password123!"),
        email_verified=True,
        is_system_admin=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_workspace(db: AsyncSession, name: str, owner_id: int) -> Workspace:
    uid = str(uuid.uuid4())[:8]
    workspace = Workspace(
        name=f"{name}_{uid}",
        description="Test workspace",
        is_private=True,
        owner_id=owner_id
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    membership = WorkspaceMembership(
        user_id=owner_id,
        workspace_id=workspace.id,
        role="owner"
    )
    db.add(membership)
    await db.commit()
    return workspace


async def test_login_sets_httponly_and_csrf_cookies(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "logincookie")
    
    response = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "access_token_cookie" in response.cookies
    assert "csrf_token" in response.cookies


async def test_logout_clears_cookies(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "logoutcookie")
    
    login_res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert login_res.status_code == 200

    logout_res = await client.post("/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Logged out successfully"


async def test_csrf_validation_on_state_changing_cookie_requests(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "csrfuser")
    
    login_res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert login_res.status_code == 200

    csrf_token = login_res.cookies.get("csrf_token")
    assert csrf_token is not None

    # Request with matching X-CSRF-Token header -> Should succeed
    res_with_csrf = await client.post(
        "/auth/ws-ticket",
        json={"workspace_id": 1},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert res_with_csrf.status_code == 200
    assert "ticket" in res_with_csrf.json()

    # Request with missing or bad X-CSRF-Token header -> Should be rejected with HTTP 403
    res_bad_csrf = await client.post(
        "/auth/ws-ticket",
        json={"workspace_id": 1},
        headers={"X-CSRF-Token": "invalid_csrf_token"}
    )
    assert res_bad_csrf.status_code == 403


async def test_ws_ticket_generation_and_validation(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "ticketuser")
    workspace = await _create_workspace(db_session, "Ticket WS", user.id)

    login_res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert login_res.status_code == 200
    csrf_token = login_res.cookies.get("csrf_token")

    ticket_res = await client.post(
        "/auth/ws-ticket",
        json={"workspace_id": workspace.id},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert ticket_res.status_code == 200
    data = ticket_res.json()
    assert "ticket" in data
    assert data["expires_in"] == 60

    # Validate ticket decoding
    ticket_payload = decode_websocket_ticket(data["ticket"])
    assert ticket_payload["sub"] == user.email
    assert ticket_payload["workspace_id"] == workspace.id
    assert ticket_payload["token_type"] == "ws_ticket"


async def test_invalid_ws_ticket_rejected():
    with pytest.raises(TokenDecodeError):
        decode_websocket_ticket("invalid.ws.ticket")
