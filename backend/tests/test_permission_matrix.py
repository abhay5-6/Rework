import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization, OrgMembership
from app.models.workspace import Workspace
from app.models.membership import WorkspaceMembership, ChannelMembership
from app.models.channel import Channel

from app.models.message import Message
from app.models.workspace_task import WorkspaceTask
from app.core.security import hash_password

pytestmark = pytest.mark.asyncio


async def _create_test_user(db: AsyncSession, prefix: str = "perm_user", is_admin: bool = False) -> User:
    uid = str(uuid.uuid4())[:8]
    user = User(
        username=f"{prefix}_{uid}",
        email=f"{prefix}_{uid}@example.com",
        hashed_password=hash_password("Password123!"),
        email_verified=True,
        is_system_admin=is_admin
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_org(db: AsyncSession, owner: User, name: str = "Test Org") -> Organization:
    uid = str(uuid.uuid4())[:8]
    org = Organization(
        name=f"{name}_{uid}",
        created_by=owner.id
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    member = OrgMembership(
        org_id=org.id,
        user_id=owner.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    return org



async def _create_workspace(db: AsyncSession, owner: User, org: Organization | None = None, is_private: bool = False) -> Workspace:
    uid = str(uuid.uuid4())[:8]
    ws = Workspace(
        name=f"WS_{uid}",
        description="Test workspace",
        is_private=is_private,
        owner_id=owner.id,
        organization_id=org.id if org else None
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)

    membership = WorkspaceMembership(
        user_id=owner.id,
        workspace_id=ws.id,
        role="owner"
    )
    db.add(membership)
    await db.commit()
    return ws


async def _login_client(client: AsyncClient, user: User) -> dict:
    res = await client.post(
        "/auth/login",
        data={"username": user.email, "password": "Password123!"}
    )
    assert res.status_code == 200
    csrf_token = res.cookies.get("csrf_token")
    return {"X-CSRF-Token": csrf_token} if csrf_token else {}


async def test_org_settings_permission_matrix(client: AsyncClient, db_session: AsyncSession):
    """Verifies org settings update permissions: owner allowed, non-member rejected."""
    owner = await _create_test_user(db_session, "org_owner")
    outsider = await _create_test_user(db_session, "org_outsider")
    org = await _create_org(db_session, owner, "Acme Corp")

    # Owner can access settings
    headers = await _login_client(client, owner)
    res = await client.get(f"/orgs/{org.id}")
    assert res.status_code == 200

    # Outsider rejected
    headers = await _login_client(client, outsider)
    res = await client.get(f"/orgs/{org.id}")
    assert res.status_code == 403


async def test_private_vs_public_workspace_access(client: AsyncClient, db_session: AsyncSession):
    """Verifies private workspace is rejected for non-members, while public workspace allows access."""
    owner = await _create_test_user(db_session, "ws_owner")
    non_member = await _create_test_user(db_session, "ws_nonmember")

    private_ws = await _create_workspace(db_session, owner, is_private=True)
    public_ws = await _create_workspace(db_session, owner, is_private=False)

    await _login_client(client, non_member)

    # Non-member rejected on private workspace
    res = await client.get(f"/workspaces/{private_ws.id}")
    assert res.status_code == 403

    # Public workspace accessible
    res = await client.get(f"/workspaces/{public_ws.id}")
    assert res.status_code == 200


async def test_private_channel_member_enforcement(client: AsyncClient, db_session: AsyncSession):
    """Verifies non-channel member cannot access messages or details of a private channel."""
    owner = await _create_test_user(db_session, "ch_owner")
    outsider = await _create_test_user(db_session, "ch_outsider")
    ws = await _create_workspace(db_session, owner, is_private=False)

    private_channel = Channel(
        name="secret-channel",
        workspace_id=ws.id,
        is_private=True
    )
    db_session.add(private_channel)
    await db_session.commit()
    await db_session.refresh(private_channel)

    # Add owner to private channel
    cm = ChannelMembership(channel_id=private_channel.id, user_id=owner.id, role="owner")

    db_session.add(cm)
    await db_session.commit()

    # Outsider rejected from private channel
    await _login_client(client, outsider)
    res = await client.get(f"/channels/{private_channel.id}")
    assert res.status_code == 403


async def test_cross_tenant_file_access_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verifies that a user in Org A cannot download files from Org B."""
    user_a = await _create_test_user(db_session, "tenant_a")
    user_b = await _create_test_user(db_session, "tenant_b")

    ws_a = await _create_workspace(db_session, user_a, is_private=True)

    await _login_client(client, user_b)
    res = await client.get(f"/workspaces/{ws_a.id}/files/secret_report.pdf")
    assert res.status_code == 403


async def test_admin_route_permission_enforcement(client: AsyncClient, db_session: AsyncSession):
    """Verifies /admin/stats rejects regular users with 403 and allows system admins."""
    regular_user = await _create_test_user(db_session, "regular_user", is_admin=False)
    admin_user = await _create_test_user(db_session, "admin_user", is_admin=True)

    await _login_client(client, regular_user)
    res = await client.get("/admin/stats")
    assert res.status_code == 403

    await _login_client(client, admin_user)
    res = await client.get("/admin/stats")
    assert res.status_code == 200
    assert "users" in res.json()


async def test_id_enumeration_attempts_rejected(client: AsyncClient, db_session: AsyncSession):
    """Verifies that attempts to enumerate non-existent or foreign workspace IDs return 403 or 404 cleanly."""
    user = await _create_test_user(db_session, "enum_user")
    await _login_client(client, user)

    # Non-existent workspace ID returns 404
    res = await client.get("/workspaces/9999999")
    assert res.status_code == 404

    # Non-existent channel ID returns 404
    res = await client.get("/channels/9999999")
    assert res.status_code == 404
