import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.message import MessageCreate
from app.repositories.workspace_repository import workspace_repo
from app.repositories.membership_repository import membership_repo
from app.repositories.message_repository import message_repo

logger = logging.getLogger(__name__)


async def has_workspace_access(
    db: AsyncSession,
    workspace_id: int,
    user: User
) -> bool:
    """
    Checks if a user has access to a specific workspace.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace to check.
        user: The user attempting to access the workspace.
        
    Returns:
        True if the user has access (either public workspace or member of private workspace), False otherwise.
    """
    workspace = await workspace_repo.get(db, id=workspace_id)
    if not workspace:
        logger.warning("Workspace not found during access check", extra={"workspace_id": workspace_id, "user_id": user.id})
        return False

    # PUBLIC WORKSPACE - allow access
    if not workspace.is_private:
        return True

    # PRIVATE WORKSPACE - check membership
    membership = await membership_repo.get_membership(db, workspace_id=workspace_id, user_id=user.id)
    if not membership:
        logger.info("Access denied: User is not a member of private workspace", extra={"workspace_id": workspace_id, "user_id": user.id})
    return membership is not None


async def send_message(
    db: AsyncSession,
    workspace_id: int,
    user: User,
    message_data: MessageCreate
):
    """
    Sends a new message to a workspace via the REST API.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace to send the message to.
        user: The user sending the message.
        message_data: The message content and metadata.
        
    Returns:
        The created Message object, or None if the user does not have access.
    """
    allowed = await has_workspace_access(db, workspace_id, user)
    if not allowed:
        return None

    message = await message_repo.create(
        db,
        obj_in={
            "content": message_data.content,
            "sender_id": user.id,
            "workspace_id": workspace_id,
            "channel_id": getattr(message_data, 'channel_id', None)
        }
    )
    logger.info("Message sent via REST", extra={"message_id": message.id, "workspace_id": workspace_id, "user_id": user.id})
    return message


async def get_workspace_messages(
    db: AsyncSession,
    workspace_id: int,
    user: User,
    limit: int = 50,
    offset: int = 0
):
    """
    Retrieves a paginated list of messages for a workspace.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        user: The user requesting the messages.
        limit: Maximum number of messages to return.
        offset: Number of messages to skip.
        
    Returns:
        A list of formatted message dictionaries, oldest first, or None if access is denied.
    """
    allowed = await has_workspace_access(db, workspace_id, user)
    if not allowed:
        return None

    # Note: message_repo.get_messages_for_workspace currently orders by desc, but old code orders by asc
    # We will adjust the logic to match the repository method which handles pagination
    messages = await message_repo.get_messages_for_workspace(
        db, workspace_id=workspace_id, skip=offset, limit=limit
    )

    formatted_messages = []
    for message, username in messages:
        formatted_messages.append({
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "workspace_id": message.workspace_id,
            "channel_id": message.channel_id,
            "created_at": message.created_at,
            "username": username if username else "Rework AI",
            "extra_data": message.extra_data
        })
    
    # Reverse to return oldest first if that's what the UI expects, since repo ordered desc for pagination
    formatted_messages.reverse()
    logger.debug("Fetched workspace messages", extra={"workspace_id": workspace_id, "user_id": user.id, "count": len(formatted_messages)})
    return formatted_messages


async def create_realtime_message(
    db: AsyncSession,
    workspace_id: int,
    user: User | None,
    content: str,
    extra_data: dict = None,
    channel_id: int | None = None
):
    """
    Creates a new message originating from a WebSocket connection or AI system.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        user: The user sending the message, or None if sent by the AI.
        content: The text content of the message.
        extra_data: Optional dictionary containing file attachments or AI metadata.
        channel_id: Optional channel ID to scope the message.
        
    Returns:
        The created Message object, or None if the user does not have access.
    """
    if user is not None:
        allowed = await has_workspace_access(db, workspace_id, user)
        if not allowed:
            logger.warning("WebSocket message creation denied", extra={"workspace_id": workspace_id, "user_id": user.id})
            return None

    message = await message_repo.create(
        db,
        obj_in={
            "content": content,
            "sender_id": user.id if user else None,
            "workspace_id": workspace_id,
            "channel_id": channel_id,
            "extra_data": extra_data or {}
        }
    )
    
    logger.info(
        "Realtime message created", 
        extra={
            "message_id": message.id, 
            "workspace_id": workspace_id, 
            "user_id": user.id if user else "AI",
            "has_extra_data": bool(extra_data)
        }
    )
    return message
