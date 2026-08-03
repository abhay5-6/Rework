from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.channel import Channel
from app.schemas.channel import ChannelCreate
from app.repositories.membership_repository import membership_repo
from app.repositories.channel_repository import channel_repo

async def create_channel(db: AsyncSession, channel_in: ChannelCreate, current_user_id: int) -> Channel:
    # Verify the user is a member of the workspace
    membership = await membership_repo.get_membership(db, workspace_id=channel_in.workspace_id, user_id=current_user_id)
    if not membership and not hasattr(current_user_id, 'is_system_admin'): # System admins bypass this in the caller, but here we just have ID
        pass # Actually we'll assume the caller passes system admins through
        
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
        
    from sqlalchemy import select
    from app.models.workspace import Workspace
    from app.models.organization import Organization, OrgMembership
    from app.utils.permissions import is_admin
    
    workspace = (await db.execute(select(Workspace).where(Workspace.id == channel_in.workspace_id))).scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    if channel_in.is_private:
        org = (await db.execute(select(Organization).where(Organization.id == workspace.org_id))).scalar_one_or_none()
        
        # Check if user is org admin
        org_membership = (await db.execute(
            select(OrgMembership).where(OrgMembership.org_id == workspace.org_id, OrgMembership.user_id == current_user_id)
        )).scalar_one_or_none()
        
        is_org_admin = org_membership and org_membership.role in ["owner", "admin"]
        
        if not is_org_admin and org and not org.allow_private_channels:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization does not allow members to create private channels. Request approval from an administrator."
            )

    channel = await channel_repo.create(
        db,
        obj_in={
            "name": channel_in.name,
            "description": channel_in.description,
            "workspace_id": channel_in.workspace_id,
            "is_private": channel_in.is_private
        }
    )
    
    # Automatically add the creator to the private channel
    if channel_in.is_private:
        from app.models.membership import ChannelMembership
        cm = ChannelMembership(user_id=current_user_id, channel_id=channel.id, role="admin")
        db.add(cm)
        await db.commit()
        
    return channel

async def get_workspace_channels(db: AsyncSession, workspace_id: int, current_user_id: int):
    # Verify workspace membership
    membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=current_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    channels = await channel_repo.get_channels_for_workspace(db, workspace_id=workspace_id)
    
    # Filter private channels
    from app.utils.permissions import is_admin
    if is_admin(membership):
        return channels # Workspace admins see all channels
        
    from sqlalchemy import select
    from app.models.membership import ChannelMembership
    
    cm_results = await db.execute(
        select(ChannelMembership.channel_id).where(ChannelMembership.user_id == current_user_id)
    )
    user_private_channel_ids = {row for row in cm_results.scalars()}
    
    filtered_channels = []
    for channel in channels:
        if not channel.is_private or channel.id in user_private_channel_ids:
            filtered_channels.append(channel)
            
    return filtered_channels

