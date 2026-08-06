from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.channel import ChannelSchema, ChannelCreate, ChannelMemberResponse, ChannelMemberCreate
from app.services import channel_service
from app.core.dependencies import get_current_user, verify_channel_access
from app.models.user import User
from app.utils.permissions import require_channel_admin

router = APIRouter()

@router.post("/", response_model=ChannelSchema)
async def create_channel(
    channel_in: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await channel_service.create_channel(db, channel_in, current_user.id)

@router.get("/workspace/{workspace_id}", response_model=List[ChannelSchema])
async def get_workspace_channels(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await channel_service.get_workspace_channels(db, workspace_id, current_user.id)

@router.get("/{channel_id}", response_model=ChannelSchema)
async def get_channel_details(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    channel = await verify_channel_access(db, channel_id, current_user)
    return channel

@router.get("/{channel_id}/members", response_model=List[ChannelMemberResponse])
async def get_channel_members(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_channel_access(db, channel_id, current_user)
    return await channel_service.get_channel_members(db, channel_id, current_user)

@router.post(
    "/{channel_id}/members", 
    dependencies=[Depends(require_channel_admin)]
)
async def add_channel_member(
    channel_id: int,
    member_in: ChannelMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_channel_access(db, channel_id, current_user)
    result = await channel_service.add_channel_member(db, channel_id, member_in.user_id, current_user)
    if result == "user_not_in_workspace":
        raise HTTPException(status_code=400, detail="User is not a member of the workspace")
    if result == "already_member":
        raise HTTPException(status_code=400, detail="User is already a member of this channel")
    return {"message": "Member added"}

@router.delete(
    "/{channel_id}/members/{user_id}",
    dependencies=[Depends(require_channel_admin)]
)
async def remove_channel_member(
    channel_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_channel_access(db, channel_id, current_user)
    result = await channel_service.remove_channel_member(db, channel_id, user_id, current_user)
    if result == "member_not_found":
        raise HTTPException(status_code=404, detail="Member not found")
    if result == "cannot_remove_self":
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    return {"message": "Member removed"}
