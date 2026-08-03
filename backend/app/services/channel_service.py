from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.channel import Channel
from app.schemas.channel import DeskCreate
from app.repositories.membership_repository import membership_repo
from app.repositories.channel_repository import channel_repo

async def create_channel(db: AsyncSession, channel_in: DeskCreate, current_user_id: int) -> Channel:
    # Verify the user is a member of the workspace
    membership = await membership_repo.get_membership(db, workspace_id=channel_in.workspace_id, user_id=current_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )

    channel = await channel_repo.create(
        db,
        obj_in={
            "name": channel_in.name,
            "description": channel_in.description,
            "workspace_id": channel_in.workspace_id
        }
    )
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
    return channels

