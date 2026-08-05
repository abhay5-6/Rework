from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.membership import (
    WorkspaceMembership
)
from app.models.user import User


async def get_membership(
    db: AsyncSession,
    workspace_id: int,
    user_id: int
):

    result = await db.execute(

        select(WorkspaceMembership)
        .where(
            WorkspaceMembership.workspace_id
                == workspace_id,

            WorkspaceMembership.user_id
                == user_id
        )
    )

    return result.scalar_one_or_none()


def is_owner(
    membership: WorkspaceMembership | None
) -> bool:
    """Check if user is workspace owner"""
    return (
        membership is not None
        and membership.role == "owner"
    )


def is_workspace_owner(
    membership: WorkspaceMembership | None
):
    """Alias for is_owner - for backward compatibility"""
    return is_owner(membership)


def is_admin(
    membership: WorkspaceMembership | None
) -> bool:
    """Check if user is workspace admin or owner"""
    return (
        membership is not None
        and membership.role in [
            "owner",
            "admin"
        ]
    )


def is_workspace_admin(
    membership: WorkspaceMembership | None
):
    """Alias for is_admin - for backward compatibility"""
    return is_admin(membership)


def can_manage_workspace(
    membership: WorkspaceMembership | None
):

    return is_workspace_admin(
        membership
    )


async def require_workspace_owner(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceMembership:
    membership = await get_membership(db, workspace_id, current_user.id)
    if not is_owner(membership):
        raise HTTPException(
            status_code=403,
            detail="Only owner can perform this action",
        )
    return membership


async def require_workspace_admin(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceMembership:
    membership = await get_membership(db, workspace_id, current_user.id)
    if not is_admin(membership) and not current_user.is_system_admin:
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )
    return membership


async def require_system_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=403,
            detail="System Administrator privileges required",
        )
    return current_user


from app.models.organization import OrgMembership
async def require_org_admin(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMembership:
    if current_user.is_system_admin:
        return OrgMembership(user_id=current_user.id, org_id=org_id, role="owner")
        
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == current_user.id
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Organization Administrator privileges required",
        )
    return membership


from app.models.membership import ChannelMembership
from app.models.channel import Channel
async def require_channel_access(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_system_admin:
        return True
        
    # Check if channel is private
    channel_result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    if not channel.is_private:
        # Check workspace membership if channel is public
        ws_membership = await get_membership(db, channel.workspace_id, current_user.id)
        if not ws_membership:
            raise HTTPException(status_code=403, detail="Workspace access required")
        return True
        
    # If private, require ChannelMembership or Workspace Admin
    ws_membership = await get_membership(db, channel.workspace_id, current_user.id)
    if is_admin(ws_membership):
        return True
        
    cm_result = await db.execute(
        select(ChannelMembership).where(
            ChannelMembership.channel_id == channel_id,
            ChannelMembership.user_id == current_user.id
        )
    )
from enum import Enum

class WorkspaceRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"

class ChannelRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class OrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

def has_workspace_role(membership: WorkspaceMembership | None, min_role: WorkspaceRole) -> bool:
    """Check if user has at least the specified workspace role."""
    if not membership:
        return False
        
    role_hierarchy = {
        WorkspaceRole.OWNER: 4,
        WorkspaceRole.ADMIN: 3,
        WorkspaceRole.CONTRIBUTOR: 2,
        WorkspaceRole.VIEWER: 1
    }
    
    user_level = role_hierarchy.get(WorkspaceRole(membership.role), 0)
    required_level = role_hierarchy.get(min_role, 99)
    
    return user_level >= required_level

def require_workspace_role(min_role: WorkspaceRole):
    """Dependency factory for checking granular workspace roles."""
    async def role_checker(
        workspace_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> WorkspaceMembership:
        if current_user.is_system_admin:
            return WorkspaceMembership(user_id=current_user.id, workspace_id=workspace_id, role=WorkspaceRole.OWNER)
            
        membership = await get_membership(db, workspace_id, current_user.id)
        if not has_workspace_role(membership, min_role):
            raise HTTPException(
                status_code=403,
                detail=f"Requires at least {min_role.value} role",
            )
        return membership
    return role_checker

async def require_channel_admin(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ensure user is an admin of the channel, or an admin of the workspace."""
    if current_user.is_system_admin:
        return True
        
    # Check channel
    channel_result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    # Check workspace admin
    ws_membership = await get_membership(db, channel.workspace_id, current_user.id)
    if is_admin(ws_membership):
        return True
        
    # Check channel admin
    cm_result = await db.execute(
        select(ChannelMembership).where(
            ChannelMembership.channel_id == channel_id,
            ChannelMembership.user_id == current_user.id
        )
    )
    cm = cm_result.scalar_one_or_none()
    if not cm or cm.role != ChannelRole.ADMIN:
        raise HTTPException(status_code=403, detail="Channel Administrator privileges required")
        
    return True