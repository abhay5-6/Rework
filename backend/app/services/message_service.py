import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.message import MessageCreate
from app.repositories.room_repository import room_repo
from app.repositories.membership_repository import membership_repo
from app.repositories.message_repository import message_repo

logger = logging.getLogger(__name__)


async def has_room_access(
    db: AsyncSession,
    room_id: int,
    user: User
) -> bool:
    """
    Checks if a user has access to a specific room.
    
    Args:
        db: Database session.
        room_id: ID of the room to check.
        user: The user attempting to access the room.
        
    Returns:
        True if the user has access (either public room or member of private room), False otherwise.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        logger.warning("Room not found during access check", extra={"room_id": room_id, "user_id": user.id})
        return False

    # PUBLIC ROOM - allow access
    if not room.is_private:
        return True

    # PRIVATE ROOM - check membership
    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=user.id)
    if not membership:
        logger.info("Access denied: User is not a member of private room", extra={"room_id": room_id, "user_id": user.id})
    return membership is not None


async def send_message(
    db: AsyncSession,
    room_id: int,
    user: User,
    message_data: MessageCreate
):
    """
    Sends a new message to a room via the REST API.
    
    Args:
        db: Database session.
        room_id: ID of the room to send the message to.
        user: The user sending the message.
        message_data: The message content and metadata.
        
    Returns:
        The created Message object, or None if the user does not have access.
    """
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
    logger.info("Message sent via REST", extra={"message_id": message.id, "room_id": room_id, "user_id": user.id})
    return message


async def get_room_messages(
    db: AsyncSession,
    room_id: int,
    user: User,
    limit: int = 50,
    offset: int = 0
):
    """
    Retrieves a paginated list of messages for a room.
    
    Args:
        db: Database session.
        room_id: ID of the room.
        user: The user requesting the messages.
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.
        
    Returns:
        A list of formatted message dictionaries, oldest first, or None if access is denied.
    """
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
    logger.debug("Fetched room messages", extra={"room_id": room_id, "user_id": user.id, "count": len(formatted_messages)})
    return formatted_messages


async def create_realtime_message(
    db: AsyncSession,
    room_id: int,
    user: User | None,
    content: str,
    extra_data: dict = None,
    desk_id: int | None = None
):
    """
    Creates a new message originating from a WebSocket connection or AI system.
    
    Args:
        db: Database session.
        room_id: ID of the room.
        user: The user sending the message, or None if sent by the AI.
        content: The text content of the message.
        extra_data: Optional dictionary containing file attachments or AI metadata.
        desk_id: Optional desk ID to scope the message.
        
    Returns:
        The created Message object, or None if the user does not have access.
    """
    if user is not None:
        allowed = await has_room_access(db, room_id, user)
        if not allowed:
            logger.warning("WebSocket message creation denied", extra={"room_id": room_id, "user_id": user.id})
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
    
    logger.info(
        "Realtime message created", 
        extra={
            "message_id": message.id, 
            "room_id": room_id, 
            "user_id": user.id if user else "AI",
            "has_extra_data": bool(extra_data)
        }
    )
    return message
