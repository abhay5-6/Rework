from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.permissions import (
    is_workspace_owner,
    is_workspace_admin
)
from app.repositories.workspace_repository import workspace_repo
from app.repositories.membership_repository import membership_repo


async def get_workspace_members(
    db: AsyncSession,
    workspace_id: int,
    current_user: User
):
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        return None

    # PUBLIC WORKSPACE
    if not workspace.is_private:
        allowed = True
    else:
        membership_check = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user.id)
        allowed = membership_check is not None

    if not allowed:
        return None

    members = await membership_repo.get_workspace_members_with_users(db, workspace_id=workspace_id)

    formatted_members = []
    for membership, user in members:
        formatted_members.append({
            "user_id": user.id,
            "username": user.username,
            "role": membership.role
        })

    return formatted_members


async def promote_member(
    db: AsyncSession,
    workspace_id: int,
    target_user_id: int,
    current_user: User
):
    current_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user.id)
    if not is_workspace_owner(current_membership):
        return "not_owner"

    target_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=target_user_id)
    if not target_membership:
        return "member_not_found"
    if target_membership.role == "owner":
        return "cannot_modify_owner"
    if target_membership.role == "admin":
        return "already_admin"

    target_membership.role = "admin"
    await db.commit()
    return "promoted"


async def demote_member(
    db: AsyncSession,
    workspace_id: int,
    target_user_id: int,
    current_user: User
):
    current_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user.id)
    if not is_workspace_owner(current_membership):
        return "not_owner"

    if target_user_id == current_user.id:
        return "cannot_demote_self"

    target_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=target_user_id)
    if not target_membership:
        return "member_not_found"
    if target_membership.role == "owner":
        return "cannot_modify_owner"
    if target_membership.role == "member":
        return "already_member"

    target_membership.role = "member"
    await db.commit()
    return "demoted"


async def remove_member(
    db: AsyncSession,
    workspace_id: int,
    target_user_id: int,
    current_user: User
):
    current_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user.id)
    if not is_workspace_admin(current_membership):
        return "not_authorized"

    if target_user_id == current_user.id:
        return "cannot_remove_self"

    target_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=target_user_id)
    if not target_membership:
        return "member_not_found"
    if target_membership.role == "owner":
        return "cannot_remove_owner"
    if current_membership.role == "admin" and target_membership.role == "admin":
        return "cannot_remove_admin"

    await membership_repo.remove(db, id=target_membership.id)
    return "removed"

