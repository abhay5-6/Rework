from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.membership import RoomMembership
from app.models.user import User
from app.models.room import Room
from app.schemas.message import MessageCreate


async def has_room_access(
    db: AsyncSession,
    room_id: int,
    user: User
):
    # Use JOIN to prevent race condition
    # between checking room existence and membership
    from sqlalchemy.orm import joinedload
    from sqlalchemy import and_
    
    result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    room = result.scalar()

    if not room:
        return False

    # PUBLIC ROOM - allow access
    if not room.is_private:
        return True

    # PRIVATE ROOM - check membership in same transaction
    membership_result = await db.execute(
        select(RoomMembership).where(
            and_(
                RoomMembership.user_id == user.id,
                RoomMembership.room_id == room_id
            )
        )
    )

    membership = membership_result.scalar()

    return membership is not None


async def send_message(
    db: AsyncSession,
    room_id: int,
    user: User,
    message_data: MessageCreate
):

    allowed = await has_room_access(
        db,
        room_id,
        user
    )

    if not allowed:
        return None

    message = Message(
        content=message_data.content,
        sender_id=user.id,
        room_id=room_id,
        desk_id=getattr(message_data, 'desk_id', None)
    )

    db.add(message)

    await db.flush()

    await db.refresh(message)
    
    return message


async def get_room_messages(
    db: AsyncSession,
    room_id: int,
    user: User,
    limit: int = 50,
    offset: int = 0
):

    allowed = await has_room_access(
        db,
        room_id,
        user
    )

    if not allowed:
        return None

    stmt = (
        select(Message, User)
        .outerjoin(User, Message.sender_id == User.id)
        .where(Message.room_id == room_id)
    )

    stmt = stmt.order_by(Message.created_at).offset(offset).limit(limit)
    result = await db.execute(stmt)

    messages = result.all()

    formatted_messages = []

    for message, sender in messages:

        formatted_messages.append({

            "id": message.id,

            "content": message.content,

            "sender_id": message.sender_id,

            "room_id": message.room_id,

            "desk_id": message.desk_id,

            "created_at":
                message.created_at,

            "username":
                sender.username if sender else "Rework AI",
                
            "extra_data": message.extra_data
        })

    return formatted_messages


async def create_realtime_message(
    db: AsyncSession,
    room_id: int,
    user: User | None,
    content: str,
    extra_data: dict = None,
    desk_id: int | None = None
):
    if user is not None:
        allowed = await has_room_access(
            db,
            room_id,
            user
        )

        if not allowed:
            return None

    message = Message(
        content=content,
        sender_id=user.id if user else None,
        room_id=room_id,
        desk_id=desk_id,
        extra_data=extra_data or {}
    )

    db.add(message)

    await db.flush()

    await db.refresh(message)

 

    return message
