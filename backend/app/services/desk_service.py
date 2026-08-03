from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.desk import Desk
from app.schemas.desk import DeskCreate
from app.repositories.membership_repository import membership_repo
from app.repositories.desk_repository import desk_repo

async def create_desk(db: AsyncSession, desk_in: DeskCreate, current_user_id: int) -> Desk:
    # Verify the user is a member of the room
    membership = await membership_repo.get_membership(db, room_id=desk_in.room_id, user_id=current_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this room"
        )

    desk = await desk_repo.create(
        db,
        obj_in={
            "name": desk_in.name,
            "description": desk_in.description,
            "room_id": desk_in.room_id
        }
    )
    return desk

async def get_room_desks(db: AsyncSession, room_id: int, current_user_id: int):
    # Verify room membership
    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=current_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this room"
        )

    desks = await desk_repo.get_desks_for_room(db, room_id=room_id)
    return desks

