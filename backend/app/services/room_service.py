import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.desk import Desk
from app.models.message import Message
from app.schemas.room import RoomCreate
from app.models.user import User

from app.repositories.room_repository import room_repo
from app.repositories.membership_repository import membership_repo
from app.repositories.join_request_repository import join_request_repo
from app.repositories.org_repository import org_membership_repo

from app.services.join_request_service import create_join_request
from app.core.exceptions import (
    RoomAlreadyExistsException,
    RoomAlreadyJoinedException,
    RoomMembershipRequiredException,
    RoomNotFoundException,
    RoomOwnerCannotLeaveException,
    RoomOwnerRequiredException,
    OrganizationMembershipRequiredException,
)

logger = logging.getLogger(__name__)


async def create_room(
    db: AsyncSession,
    room_data: RoomCreate,
    creator: User
) -> Room:
    """
    Creates a new room, assigns the creator as the owner, and auto-creates a default desk.
    
    Args:
        db: Database session.
        room_data: Schema containing room details (name, description, etc.).
        creator: The user creating the room.
        
    Returns:
        The newly created Room object.
        
    Raises:
        OrganizationMembershipRequiredException: If organization_id is provided but the creator is not a member.
        RoomAlreadyExistsException: If a room with the same name already exists in the same scope.
    """
    if room_data.organization_id is not None:
        org_mem = await org_membership_repo.get_membership(
            db, org_id=room_data.organization_id, user_id=creator.id
        )
        if not org_mem:
            logger.warning("Room creation failed: Not an org member", extra={"org_id": room_data.organization_id, "user_id": creator.id})
            raise OrganizationMembershipRequiredException()

    # Check for existing room
    query = select(Room).where(Room.name == room_data.name)
    if room_data.organization_id is not None:
        query = query.where(Room.organization_id == room_data.organization_id)
        
    existing_room = await db.execute(query)
    if existing_room.scalar():
        logger.warning("Room creation failed: Name collision", extra={"room_name": room_data.name})
        raise RoomAlreadyExistsException()

    room = await room_repo.create(
        db,
        obj_in={
            "name": room_data.name,
            "description": room_data.description,
            "is_private": room_data.is_private,
            "ai_enabled": room_data.ai_enabled,
            "organization_id": room_data.organization_id,
            "owner_id": creator.id
        }
    )

    await membership_repo.create(
        db,
        obj_in={
            "user_id": creator.id,
            "room_id": room.id,
            "role": "owner"
        }
    )

    # Auto-create default desk
    default_desk = Desk(
        name="general",
        description="General discussion channel",
        room_id=room.id
    )
    db.add(default_desk)

    await db.commit()
    await db.refresh(room)
    
    logger.info("Room created successfully", extra={"room_id": room.id, "room_name": room.name, "owner_id": creator.id})
    return room


async def get_rooms(
    db: AsyncSession,
    current_user: User,
    organization_id: int | None = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Retrieves a paginated list of rooms visible to the current user.
    
    Args:
        db: Database session.
        current_user: The user requesting the list.
        organization_id: Optional org ID to filter rooms by organization.
        skip: Pagination offset.
        limit: Pagination limit.
        
    Returns:
        A dictionary containing the 'items' (list of room dicts) and 'total' count.
    """
    if organization_id is not None:
        org_mem = await org_membership_repo.get_membership(
            db, org_id=organization_id, user_id=current_user.id
        )
        if not org_mem:
            return {"items": [], "total": 0}

    total_rooms = await room_repo.get_rooms_count(db, organization_id=organization_id)
    rooms = await room_repo.get_paginated_rooms(db, organization_id=organization_id, skip=skip, limit=limit)

    memberships = await membership_repo.get_user_memberships(db, user_id=current_user.id)
    
    # Needs custom query to get all user's pending requests (join_request_repo)
    requests_result = await db.execute(
        select(join_request_repo.model).where(
            join_request_repo.model.user_id == current_user.id,
            join_request_repo.model.status == "pending"
        )
    )
    pending_requests = requests_result.scalars().all()

    # Build maps for fast lookup
    membership_map = {m.room_id: m for m in memberships}
    pending_request_map = {r.room_id: r for r in pending_requests}

    room_list = []
    for room in rooms:
        membership = membership_map.get(room.id)
        pending_request = pending_request_map.get(room.id)

        room_list.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "is_private": room.is_private,
            "ai_enabled": room.ai_enabled,
            "owner_id": room.owner_id,
            "is_member": membership is not None,
            "role": membership.role if membership else None,
            "has_pending_request": pending_request is not None,
        })

    logger.debug("Fetched room list", extra={"user_id": current_user.id, "count": len(room_list)})
    return {
        "items": room_list,
        "total": total_rooms
    }


async def get_room_by_id(
    db: AsyncSession,
    room_id: int,
    current_user: User
):
    """
    Retrieves detailed information for a specific room.
    
    Args:
        db: Database session.
        room_id: The ID of the room.
        current_user: The user requesting the room details.
        
    Returns:
        A dictionary containing room details and the user's membership status, or None if not found.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        return None

    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=current_user.id)

    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "is_private": room.is_private,
        "ai_enabled": room.ai_enabled,
        "owner_id": room.owner_id,
        "is_member": membership is not None,
        "role": membership.role if membership else None
    }


async def join_room(
    db: AsyncSession,
    room_id: int,
    user: User
):
    """
    Allows a user to join a room. For public rooms, they join immediately.
    For private rooms, a join request is created instead.
    
    Args:
        db: Database session.
        room_id: The ID of the room to join.
        user: The user attempting to join.
        
    Returns:
        'joined' if joined immediately, or the JoinRequest object if a request was created.
        
    Raises:
        RoomNotFoundException: If the room does not exist.
        RoomAlreadyJoinedException: If the user is already a member.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    existing_membership = await membership_repo.get_membership(db, room_id=room_id, user_id=user.id)
    if existing_membership:
        raise RoomAlreadyJoinedException()

    # PUBLIC ROOM
    if not room.is_private:
        await membership_repo.create(
            db,
            obj_in={
                "user_id": user.id,
                "room_id": room_id,
                "role": "member"
            }
        )
        logger.info("User joined public room", extra={"room_id": room_id, "user_id": user.id})
        return "joined"

    # PRIVATE ROOM
    logger.info("User requested to join private room", extra={"room_id": room_id, "user_id": user.id})
    return await create_join_request(
        db=db,
        room_id=room_id,
        user_id=user.id,
    )


async def leave_room(
    db: AsyncSession,
    room_id: int,
    user: User
):
    """
    Allows a user to leave a room.
    
    Args:
        db: Database session.
        room_id: The ID of the room to leave.
        user: The user attempting to leave.
        
    Raises:
        RoomNotFoundException: If the room does not exist.
        RoomMembershipRequiredException: If the user is not a member.
        RoomOwnerCannotLeaveException: If the user is the owner of the room.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=user.id)
    if not membership:
        raise RoomMembershipRequiredException()

    if membership.role == "owner":
        logger.warning("Owner attempted to leave room", extra={"room_id": room_id, "user_id": user.id})
        raise RoomOwnerCannotLeaveException()

    await membership_repo.remove(db, id=membership.id)
    logger.info("User left room", extra={"room_id": room_id, "user_id": user.id})
    return "left"


async def delete_room(
    db: AsyncSession,
    room_id: int,
    user: User
):
    """
    Deletes a room and all its associated messages and memberships.
    Only the owner of the room can perform this action.
    
    Args:
        db: Database session.
        room_id: The ID of the room to delete.
        user: The user requesting the deletion (must be owner).
        
    Raises:
        RoomNotFoundException: If the room does not exist.
        RoomOwnerRequiredException: If the user is not the owner.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
        logger.warning("Non-owner attempted to delete room", extra={"room_id": room_id, "user_id": user.id})
        raise RoomOwnerRequiredException("Only owner can delete room")

    memberships = await membership_repo.get_room_members(db, room_id=room_id)
    for membership in memberships:
        await membership_repo.remove(db, id=membership.id)

    # For messages, ideally we have a message_repository, but since we don't yet, we use raw execute
    messages_result = await db.execute(
        select(Message).where(Message.room_id == room_id)
    )
    messages = messages_result.scalars().all()
    for message in messages:
        await db.delete(message)

    await room_repo.remove(db, id=room.id)
    await db.commit()
    logger.info("Room deleted", extra={"room_id": room_id, "user_id": user.id, "messages_deleted": len(messages)})
    return "deleted"


async def toggle_room_ai(
    db: AsyncSession,
    room_id: int,
    ai_enabled: bool,
    user: User
):
    """
    Toggles the AI capability on or off for a room.
    Only the owner of the room can perform this action.
    
    Args:
        db: Database session.
        room_id: The ID of the room.
        ai_enabled: The desired AI state.
        user: The user requesting the toggle (must be owner).
        
    Raises:
        RoomNotFoundException: If the room does not exist.
        RoomOwnerRequiredException: If the user is not the owner.
    """
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
        logger.warning("Non-owner attempted to toggle AI", extra={"room_id": room_id, "user_id": user.id})
        raise RoomOwnerRequiredException("Only owner can update room")

    # Using update instead of directly modifying to exercise the repository
    await room_repo.update(
        db,
        db_obj=room,
        obj_in={"ai_enabled": ai_enabled}
    )
    logger.info("Room AI toggled", extra={"room_id": room_id, "ai_enabled": ai_enabled, "user_id": user.id})
    return "updated"
