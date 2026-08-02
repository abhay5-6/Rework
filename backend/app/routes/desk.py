from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.desk import DeskSchema, DeskCreate
from app.services import desk_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=DeskSchema)
async def create_desk(
    desk_in: DeskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await desk_service.create_desk(db, desk_in, current_user.id)

@router.get("/room/{room_id}", response_model=List[DeskSchema])
async def get_room_desks(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await desk_service.get_room_desks(db, room_id, current_user.id)
