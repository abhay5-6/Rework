from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.message import MessageCreate
from app.repositories.room_repository import room_repo
from app.repositories.membership_repository import membership_repo
from app.repositories.message_repository import message_repo


async def has_room_access(
    db: AsyncSession,
    room_id: int,
    user: User
):
    room = await room_repo.get(db, id=room_id)
    if not room:
        return False

    # PUBLIC ROOM - allow access
    if not room.is_private:
        return True

    # PRIVATE ROOM - check membership
    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=user.id)
    return membership is not None


async def send_message(
    db: AsyncSession,
    room_id: int,
    user: User,
    message_data: MessageCreate
):
    allowed = await has_room_access(db, room_id, user)
    if not allowed:
        return None

    message = await message_repo.create(
        db,
        obj_in={
            "content": message_data.content,
            "sender_id": user.id,
            "room_id": room_id,
            "desk_id": getattr(message_data, 'desk_id', None)
        }
    )
    return message


async def get_room_messages(
    db: AsyncSession,
    room_id: int,
    user: User,
    limit: int = 50,
    offset: int = 0
):
    allowed = await has_room_access(db, room_id, user)
    if not allowed:
        return None

    # Note: message_repo.get_messages_for_room currently orders by desc, but old code orders by asc
    # We will adjust the logic to match the repository method which handles pagination
    messages = await message_repo.get_messages_for_room(
        db, room_id=room_id, skip=offset, limit=limit
    )

    formatted_messages = []
    for message, username in messages:
        formatted_messages.append({
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "room_id": message.room_id,
            "desk_id": message.desk_id,
            "created_at": message.created_at,
            "username": username if username else "Rework AI",
            "extra_data": message.extra_data
        })
    
    # Reverse to return oldest first if that's what the UI expects, since repo ordered desc for pagination
    formatted_messages.reverse()
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
        allowed = await has_room_access(db, room_id, user)
        if not allowed:
            return None

    message = await message_repo.create(
        db,
        obj_in={
            "content": content,
            "sender_id": user.id if user else None,
            "room_id": room_id,
            "desk_id": desk_id,
            "extra_data": extra_data or {}
        }
    )
    return message
