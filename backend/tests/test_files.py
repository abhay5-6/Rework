import pytest
import io
import os
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.membership import WorkspaceMembership
from app.models.organization import Organization, OrgMembership
from app.core.security import create_access_token, hash_password

pytestmark = pytest.mark.asyncio


async def _create_test_user(db: AsyncSession, prefix: str = "user") -> User:
    uid = str(uuid.uuid4())[:8]
    user = User(
        username=f"{prefix}_{uid}",
        email=f"{prefix}_{uid}@example.com",
        hashed_password=hash_password("password123"),
        email_verified=True,
        is_system_admin=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_workspace(
    db: AsyncSession,
    name: str,
    owner_id: int,
    is_private: bool = False,
    organization_id: int | None = None
) -> Workspace:
    uid = str(uuid.uuid4())[:8]
    workspace = Workspace(
        name=f"{name}_{uid}",
        description="Test workspace",
        is_private=is_private,
        owner_id=owner_id,
        organization_id=organization_id,
        ai_enabled=False
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


async def test_member_upload_and_download_success(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "memberuser")
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    workspace = await _create_workspace(db_session, "Member Test WS", user.id, is_private=False)

    # 1. Upload file as member
    files = {"file": ("test_doc.txt", io.BytesIO(b"Hello Rework Security"), "text/plain")}
    response = await client.post(f"/workspaces/{workspace.id}/files", files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "file_url" in data
    assert data["file_name"] == "test_doc.txt"

    file_url = data["file_url"]
    filename = os.path.basename(file_url)

    # 2. Download via Authorization Header
    download_res_header = await client.get(f"/workspaces/{workspace.id}/files/{filename}", headers=headers)
    assert download_res_header.status_code == 200
    assert download_res_header.content == b"Hello Rework Security"

    # 3. Query-string bearer tokens are intentionally rejected to prevent leakage.
    download_res_param = await client.get(f"/workspaces/{workspace.id}/files/{filename}?token={token}")
    assert download_res_param.status_code == 401


async def test_public_workspace_non_member_upload_rejected(client: AsyncClient, db_session: AsyncSession):
    owner = await _create_test_user(db_session, "owneruser")
    non_member = await _create_test_user(db_session, "nonmemberuser")

    token = create_access_token({"sub": non_member.email})
    headers = {"Authorization": f"Bearer {token}"}

    workspace = await _create_workspace(db_session, "Public WS", owner.id, is_private=False)

    files = {"file": ("unauthorized.txt", io.BytesIO(b"Unauthorized upload attempt"), "text/plain")}
    response = await client.post(f"/workspaces/{workspace.id}/files", files=files, headers=headers)
    assert response.status_code == 403
    assert "Not authorized" in response.json()["error"]["message"]


async def test_non_member_download_rejected(client: AsyncClient, db_session: AsyncSession):
    owner = await _create_test_user(db_session, "owneruser2")
    non_member = await _create_test_user(db_session, "nonmemberuser2")

    owner_token = create_access_token({"sub": owner.email})
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    non_member_token = create_access_token({"sub": non_member.email})
    non_member_headers = {"Authorization": f"Bearer {non_member_token}"}

    workspace = await _create_workspace(db_session, "Private WS", owner.id, is_private=True)

    files = {"file": ("secret.txt", io.BytesIO(b"Top Secret Data"), "text/plain")}
    upload_res = await client.post(f"/workspaces/{workspace.id}/files", files=files, headers=owner_headers)
    assert upload_res.status_code == 200
    filename = os.path.basename(upload_res.json()["file_url"])

    download_res = await client.get(f"/workspaces/{workspace.id}/files/{filename}", headers=non_member_headers)
    assert download_res.status_code == 403
    assert "Not authorized" in download_res.json()["error"]["message"]


async def test_unauthenticated_download_rejected(client: AsyncClient, db_session: AsyncSession):
    owner = await _create_test_user(db_session, "owneruser3")
    owner_token = create_access_token({"sub": owner.email})
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    workspace = await _create_workspace(db_session, "Auth Check WS", owner.id, is_private=False)

    files = {"file": ("data.txt", io.BytesIO(b"Data"), "text/plain")}
    upload_res = await client.post(f"/workspaces/{workspace.id}/files", files=files, headers=owner_headers)
    assert upload_res.status_code == 200
    filename = os.path.basename(upload_res.json()["file_url"])

    download_res = await client.get(f"/workspaces/{workspace.id}/files/{filename}")
    assert download_res.status_code == 401


async def test_removed_member_download_rejected(client: AsyncClient, db_session: AsyncSession):
    owner = await _create_test_user(db_session, "owneruser4")
    member = await _create_test_user(db_session, "memberuser4")

    workspace = await _create_workspace(db_session, "Leave WS", owner.id, is_private=False)

    membership = WorkspaceMembership(user_id=member.id, workspace_id=workspace.id, role="member")
    db_session.add(membership)
    await db_session.commit()

    member_token = create_access_token({"sub": member.email})
    member_headers = {"Authorization": f"Bearer {member_token}"}

    files = {"file": ("member_doc.txt", io.BytesIO(b"Member data"), "text/plain")}
    upload_res = await client.post(f"/workspaces/{workspace.id}/files", files=files, headers=member_headers)
    assert upload_res.status_code == 200
    filename = os.path.basename(upload_res.json()["file_url"])

    await db_session.delete(membership)
    await db_session.commit()

    download_res = await client.get(f"/workspaces/{workspace.id}/files/{filename}", headers=member_headers)
    assert download_res.status_code == 403


async def test_cross_org_file_access_rejected(client: AsyncClient, db_session: AsyncSession):
    org1_owner = await _create_test_user(db_session, "org1owner")
    org2_user = await _create_test_user(db_session, "org2user")

    org1 = Organization(name=f"Org_{uuid.uuid4()}", created_by=org1_owner.id)
    db_session.add(org1)
    await db_session.commit()

    workspace1 = await _create_workspace(db_session, "Org 1 WS", org1_owner.id, organization_id=org1.id)

    org1_token = create_access_token({"sub": org1_owner.email})
    org1_headers = {"Authorization": f"Bearer {org1_token}"}

    files = {"file": ("org1_file.txt", io.BytesIO(b"Org 1 Secret"), "text/plain")}
    upload_res = await client.post(f"/workspaces/{workspace1.id}/files", files=files, headers=org1_headers)
    assert upload_res.status_code == 200
    filename = os.path.basename(upload_res.json()["file_url"])

    org2_token = create_access_token({"sub": org2_user.email})
    org2_headers = {"Authorization": f"Bearer {org2_token}"}

    cross_upload_res = await client.post(f"/workspaces/{workspace1.id}/files", files=files, headers=org2_headers)
    assert cross_upload_res.status_code == 403

    cross_download_res = await client.get(f"/workspaces/{workspace1.id}/files/{filename}", headers=org2_headers)
    assert cross_download_res.status_code == 403


async def test_disallowed_file_extension(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "extuser")
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    workspace = await _create_workspace(db_session, "Ext Test WS", user.id)

    exe_files = {"file": ("malicious.exe", io.BytesIO(b"MZ... binary"), "application/octet-stream")}
    res_exe = await client.post(f"/workspaces/{workspace.id}/files", files=exe_files, headers=headers)
    assert res_exe.status_code == 400
    assert "not allowed" in res_exe.json()["error"]["message"]

    sh_files = {"file": ("script.sh", io.BytesIO(b"#!/bin/bash\nrm -rf /"), "text/x-shellscript")}
    res_sh = await client.post(f"/workspaces/{workspace.id}/files", files=sh_files, headers=headers)
    assert res_sh.status_code == 400
    assert "not allowed" in res_sh.json()["error"]["message"]


async def test_path_traversal_prevention(client: AsyncClient, db_session: AsyncSession):
    user = await _create_test_user(db_session, "pathuser")
    token = create_access_token({"sub": user.email})
    headers = {"Authorization": f"Bearer {token}"}

    workspace = await _create_workspace(db_session, "Path Test WS", user.id)

    download_res = await client.get(f"/workspaces/{workspace.id}/files/../secret.txt", headers=headers)
    assert download_res.status_code in (400, 404)
