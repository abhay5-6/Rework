from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.channel import DeskSchema, DeskCreate
from app.services import channel_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=DeskSchema)
async def create_channel(
    channel_in: DeskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await channel_service.create_channel(db, channel_in, current_user.id)

@router.get("/workspace/{workspace_id}", response_model=List[DeskSchema])
async def get_workspace_channels(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await channel_service.get_workspace_channels(db, workspace_id, current_user.id)
