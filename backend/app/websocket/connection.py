from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    decode_access_token
)
from app.models.user import User
from app.models.room import Room

from app.models.membership import (
    RoomMembership
)


async def authenticate_websocket(
    token: str,
    room_id: int,
    db: AsyncSession
):

    try:

        payload = decode_access_token(
            token
        )

        email = payload.get("sub")

        if not email:
            return None

    except TokenDecodeError:
        return None

    user_result = await db.execute(
        select(User).where(
            User.email == email
        )
    )

    user = user_result.scalar()

    if not user:
        return None

    room_result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    room = room_result.scalar()

    if not room:
        return None

    # PUBLIC ROOM
    if not room.is_private:
        return user

    # PRIVATE ROOM

    membership_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.user_id == user.id,
            RoomMembership.room_id == room_id
        )
    )

    membership = membership_result.scalar()

    if not membership:
        return None

    return user
