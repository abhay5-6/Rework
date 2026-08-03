import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace
from app.models.channel import Channel
from app.models.message import Message
from app.schemas.workspace import RoomCreate
from app.models.user import User

from app.repositories.workspace_repository import workspace_repo
from app.repositories.membership_repository import membership_repo
from app.repositories.join_request_repository import join_request_repo
from app.repositories.org_repository import org_membership_repo

from app.services.join_request_service import create_join_request
from app.core.exceptions import (
    RoomAlreadyExistsException,
    RoomAlreadyJoinedException,
    WorkspaceMembershipRequiredException,
    RoomNotFoundException,
    RoomOwnerCannotLeaveException,
    RoomOwnerRequiredException,
    OrganizationMembershipRequiredException,
)

logger = logging.getLogger(__name__)


async def create_workspace(
    db: AsyncSession,
    workspace_data: RoomCreate,
    creator: User
) -> Workspace:
    """
    Creates a new workspace, assigns the creator as the owner, and auto-creates a default channel.
    
    Args:
        db: Database session.
        workspace_data: Schema containing workspace details (name, description, etc.).
        creator: The user creating the workspace.
        
    Returns:
        The newly created Workspace object.
        
    Raises:
        OrganizationMembershipRequiredException: If organization_id is provided but the creator is not a member.
        RoomAlreadyExistsException: If a workspace with the same name already exists in the same scope.
    """
    if workspace_data.organization_id is not None:
        org_mem = await org_membership_repo.get_membership(
            db, org_id=workspace_data.organization_id, user_id=creator.id
        )
        if not org_mem:
            logger.warning("Workspace creation failed: Not an org member", extra={"org_id": workspace_data.organization_id, "user_id": creator.id})
            raise OrganizationMembershipRequiredException()

    # Check for existing workspace
    query = select(Workspace).where(Workspace.name == workspace_data.name)
    if workspace_data.organization_id is not None:
        query = query.where(Workspace.organization_id == workspace_data.organization_id)
        
    existing_workspace = await db.execute(query)
    if existing_workspace.scalar():
        logger.warning("Workspace creation failed: Name collision", extra={"workspace_name": workspace_data.name})
        raise RoomAlreadyExistsException()

    workspace = await workspace_repo.create(
        db,
        obj_in={
            "name": workspace_data.name,
            "description": workspace_data.description,
            "is_private": workspace_data.is_private,
            "ai_enabled": workspace_data.ai_enabled,
            "organization_id": workspace_data.organization_id,
            "owner_id": creator.id
        }
    )

    await membership_repo.create(
        db,
        obj_in={
            "user_id": creator.id,
            "workspace_id": workspace.id,
            "role": "owner"
        }
    )

    # Auto-create default channel
    default_channel = Channel(
        name="general",
        description="General discussion channel",
        workspace_id=workspace.id
    )
    db.add(default_channel)

    await db.commit()
    await db.refresh(workspace)
    
    logger.info("Workspace created successfully", extra={"workspace_id": workspace.id, "workspace_name": workspace.name, "owner_id": creator.id})
    return workspace


async def get_workspaces(
    db: AsyncSession,
    current_user: User,
    organization_id: int | None = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieves a paginated list of workspaces visible to the current user.
    
    Args:
        db: Database session.
        current_user: The user requesting the list.
        organization_id: Optional org ID to filter workspaces by organization.
        skip: Pagination offset.
        limit: Pagination limit.
        
    Returns:
        A dictionary containing the 'items' (list of workspace dicts) and 'total' count.
    """
    if organization_id is not None:
        org_mem = await org_membership_repo.get_membership(
            db, org_id=organization_id, user_id=current_user.id
        )
        if not org_mem:
            return {"items": [], "total": 0}

    total_workspaces = await workspace_repo.get_workspaces_count(db, organization_id=organization_id)
    workspaces = await workspace_repo.get_paginated_workspaces(db, organization_id=organization_id, skip=skip, limit=limit)

    memberships = await membership_repo.get_user_memberships(db, user_id=current_user.id)
    
    # Needs custom query to get all user's pending requests (join_request_repo)
    requests_result = await db.execute(
        select(join_request_repo.model).where(
            join_request_repo.model.user_id == current_user.id,
            join_request_repo.model.status == "pending"
        )
    )
    pending_requests = requests_result.scalars().all()

    # Build maps for fast lookup
    membership_map = {m.workspace_id: m for m in memberships}
    pending_request_map = {r.workspace_id: r for r in pending_requests}

    workspace_list = []
    for workspace in workspaces:
        membership = membership_map.get(workspace.id)
        pending_request = pending_request_map.get(workspace.id)

        workspace_list.append({
            "id": workspace.id,
            "name": workspace.name,
            "description": workspace.description,
            "is_private": workspace.is_private,
            "ai_enabled": workspace.ai_enabled,
            "owner_id": workspace.owner_id,
            "is_member": membership is not None,
            "role": membership.role if membership else None,
            "has_pending_request": pending_request is not None,
        })

    logger.debug("Fetched workspace list", extra={"user_id": current_user.id, "count": len(workspace_list)})
    return {
        "items": workspace_list,
        "total": total_workspaces
    }


async def get_workspace_by_id(
    db: AsyncSession,
    workspace_id: int,
    current_user: User
):
    """
    Retrieves detailed information for a specific workspace.
    
    Args:
        db: Database session.
        workspace_id: The ID of the workspace.
        current_user: The user requesting the workspace details.
        
    Returns:
        A dictionary containing workspace details and the user's membership status, or None if not found.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        return None

    membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user.id)

    return {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "is_private": workspace.is_private,
        "ai_enabled": workspace.ai_enabled,
        "owner_id": workspace.owner_id,
        "is_member": membership is not None,
        "role": membership.role if membership else None
    }


async def join_workspace(
    db: AsyncSession,
    workspace_id: int,
    user: User
):
    """
    Allows a user to join a workspace. For public workspaces, they join immediately.
    For private workspaces, a join request is created instead.
    
    Args:
        db: Database session.
        workspace_id: The ID of the workspace to join.
        user: The user attempting to join.
        
    Returns:
        'joined' if joined immediately, or the JoinRequest object if a request was created.
        
    Raises:
        RoomNotFoundException: If the workspace does not exist.
        RoomAlreadyJoinedException: If the user is already a member.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        raise RoomNotFoundException()

    existing_membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=user.id)
    if existing_membership:
        raise RoomAlreadyJoinedException()

    # PUBLIC WORKSPACE
    if not workspace.is_private:
        await membership_repo.create(
            db,
            obj_in={
                "user_id": user.id,
                "workspace_id": workspace_id,
                "role": "member"
            }
        )
        logger.info("User joined public workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
        return "joined"

    # PRIVATE WORKSPACE
    logger.info("User requested to join private workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
    return await create_join_request(
        db=db,
        workspace_id=workspace_id,
        user_id=user.id,
    )


async def leave_workspace(
    db: AsyncSession,
    workspace_id: int,
    user: User
):
    """
    Allows a user to leave a workspace.
    
    Args:
        db: Database session.
        workspace_id: The ID of the workspace to leave.
        user: The user attempting to leave.
        
    Raises:
        RoomNotFoundException: If the workspace does not exist.
        WorkspaceMembershipRequiredException: If the user is not a member.
        RoomOwnerCannotLeaveException: If the user is the owner of the workspace.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        raise RoomNotFoundException()

    membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=user.id)
    if not membership:
        raise WorkspaceMembershipRequiredException()

    if membership.role == "owner":
        logger.warning("Owner attempted to leave workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
        raise RoomOwnerCannotLeaveException()

    await membership_repo.remove(db, id=membership.id)
    logger.info("User left workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
    return "left"


async def delete_workspace(
    db: AsyncSession,
    workspace_id: int,
    user: User
):
    """
    Deletes a workspace and all its associated messages and memberships.
    Only the owner of the workspace can perform this action.
    
    Args:
        db: Database session.
        workspace_id: The ID of the workspace to delete.
        user: The user requesting the deletion (must be owner).
        
    Raises:
        RoomNotFoundException: If the workspace does not exist.
        RoomOwnerRequiredException: If the user is not the owner.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        raise RoomNotFoundException()

    if workspace.owner_id != user.id:
        logger.warning("Non-owner attempted to delete workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
        raise RoomOwnerRequiredException("Only owner can delete workspace")

    memberships = await membership_repo.get_workspace_members(db, workspace_id=workspace_id)
    for membership in memberships:
        await membership_repo.remove(db, id=membership.id)

    # For messages, ideally we have a message_repository, but since we don't yet, we use raw execute
    messages_result = await db.execute(
        select(Message).where(Message.workspace_id == workspace_id)
    )
    messages = messages_result.scalars().all()
    for message in messages:
        await db.delete(message)

    await workspace_repo.remove(db, id=workspace.id)
    await db.commit()
    logger.info("Workspace deleted", extra={"workspace_id": workspace_id, "user_id": user.id, "messages_deleted": len(messages)})
    return "deleted"


async def toggle_workspace_ai(
    db: AsyncSession,
    workspace_id: int,
    ai_enabled: bool,
    user: User
):
    """
    Toggles the AI capability on or off for a workspace.
    Only the owner of the workspace can perform this action.
    
    Args:
        db: Database session.
        workspace_id: The ID of the workspace.
        ai_enabled: The desired AI state.
        user: The user requesting the toggle (must be owner).
        
    Raises:
        RoomNotFoundException: If the workspace does not exist.
        RoomOwnerRequiredException: If the user is not the owner.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        raise RoomNotFoundException()

    if workspace.owner_id != user.id:
        logger.warning("Non-owner attempted to toggle AI", extra={"workspace_id": workspace_id, "user_id": user.id})
        raise RoomOwnerRequiredException("Only owner can update workspace")

    # Using update instead of directly modifying to exercise the repository
    await workspace_repo.update(
        db,
        db_obj=workspace,
        obj_in={"ai_enabled": ai_enabled}
    )
    logger.info("Workspace AI toggled", extra={"workspace_id": workspace_id, "ai_enabled": ai_enabled, "user_id": user.id})
    return "updated"
