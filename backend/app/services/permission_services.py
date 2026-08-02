from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.membership import (
    RoomMembership
)


async def get_membership(
    db: AsyncSession,
    room_id: int,
    user_id: int
):

    result = await db.execute(

        select(RoomMembership).where(
            RoomMembership.room_id == room_id,
            RoomMembership.user_id == user_id
        )
    )

    return result.scalar_one_or_none()