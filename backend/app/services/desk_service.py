from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.desk import Desk
from app.models.membership import RoomMembership
from app.schemas.desk import DeskCreate

async def create_desk(db: AsyncSession, desk_in: DeskCreate, current_user_id: int) -> Desk:
    # Verify the user is a member of the room
    stmt = select(RoomMembership).where(
        RoomMembership.room_id == desk_in.room_id,
        RoomMembership.user_id == current_user_id
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this room"
        )

    desk = Desk(
        name=desk_in.name,
        description=desk_in.description,
        room_id=desk_in.room_id
    )
    db.add(desk)
    await db.commit()
    await db.refresh(desk)
    return desk

async def get_room_desks(db: AsyncSession, room_id: int, current_user_id: int):
    # Verify room membership
    stmt = select(RoomMembership).where(
        RoomMembership.room_id == room_id,
        RoomMembership.user_id == current_user_id
    )
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this room"
        )

    stmt = select(Desk).where(Desk.room_id == room_id).order_by(Desk.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()
