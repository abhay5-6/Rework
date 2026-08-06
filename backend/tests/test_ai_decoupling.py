import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.ai.embedding_service import generate_embedding
from app.models.user import User
from app.models.workspace import Workspace
from app.models.membership import WorkspaceMembership
from app.models.channel import Channel
from app.core.security import hash_password

pytestmark = pytest.mark.asyncio


async def _create_test_user(db: AsyncSession, prefix: str = "aidecouple") -> User:
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
        description="Test workspace for AI decoupling",
        is_private=False,
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


async def test_embedding_generation_in_test_mode():
    """Verifies that generate_embedding returns a mock vector instantly in test mode without network calls."""
    embedding = await generate_embedding("Rework real-time collaboration platform")
    assert isinstance(embedding, list)
    assert len(embedding) == settings.embedding_dimension
    assert embedding == [0.0] * settings.embedding_dimension


async def test_ai_disabled_route_fallback(client: AsyncClient, db_session: AsyncSession):
    """Verifies that AI routes return HTTP 503 Service Unavailable when AI features are disabled."""
    user = await _create_test_user(db_session, "aifallback")
    workspace = await _create_workspace(db_session, "AI Fallback WS", user.id)

    login_res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert login_res.status_code == 200

    # Temporarily disable AI
    original_ai_enabled = settings.ai_enabled
    object.__setattr__(settings, "ai_enabled", False)

    try:
        graph_res = await client.get(f"/ai/graph/{workspace.id}")
        assert graph_res.status_code == 503
        assert "disabled" in graph_res.json()["error"]["message"].lower()

        summary_res = await client.get(f"/ai/summary/{workspace.id}?query=test")
        assert summary_res.status_code == 503
        assert "disabled" in summary_res.json()["error"]["message"].lower()
    finally:
        object.__setattr__(settings, "ai_enabled", original_ai_enabled)



async def test_chat_works_when_ai_offline(client: AsyncClient, db_session: AsyncSession):
    """Verifies that real-time chat and message posting succeed even when AI is offline or disabled."""
    user = await _create_test_user(db_session, "chataioffline")
    workspace = await _create_workspace(db_session, "Chat Offline WS", user.id)

    channel = Channel(
        name="general",
        workspace_id=workspace.id,
        is_private=False
    )
    db_session.add(channel)
    await db_session.commit()
    await db_session.refresh(channel)

    login_res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert login_res.status_code == 200

    csrf_token = login_res.cookies.get("csrf_token")

    # Post message with AI disabled
    original_ai_enabled = settings.ai_enabled
    object.__setattr__(settings, "ai_enabled", False)

    try:
        msg_res = await client.post(
            f"/workspaces/{workspace.id}/messages",
            json={"channel_id": channel.id, "content": "Hello team, AI is offline but chat is fast!"},
            headers={"X-CSRF-Token": csrf_token}
        )


        assert msg_res.status_code == 200
        data = msg_res.json()
        assert data["content"] == "Hello team, AI is offline but chat is fast!"
    finally:
        object.__setattr__(settings, "ai_enabled", original_ai_enabled)

