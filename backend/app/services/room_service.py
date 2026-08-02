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
)


async def create_room(
    db: AsyncSession,
    room_data: RoomCreate,
    creator: User
):
    if room_data.organization_id is not None:
        org_mem = await org_membership_repo.get_membership(
            db, org_id=room_data.organization_id, user_id=creator.id
        )
        if not org_mem:
            raise RoomAlreadyExistsException()

    # Check for existing room
    query = select(Room).where(Room.name == room_data.name)
    if room_data.organization_id is not None:
        query = query.where(Room.organization_id == room_data.organization_id)
        
    existing_room = await db.execute(query)
    if existing_room.scalar():
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

    return room


async def get_rooms(
    db: AsyncSession,
    current_user: User,
    organization_id: int | None = None,
    skip: int = 0,
    limit: int = 10
):
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

    return {
        "items": room_list,
        "total": total_rooms
    }


async def get_room_by_id(
    db: AsyncSession,
    room_id: int,
    current_user: User
):
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
        return "joined"

    # PRIVATE ROOM
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
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    membership = await membership_repo.get_membership(db, room_id=room_id, user_id=user.id)
    if not membership:
        raise RoomMembershipRequiredException()

    if membership.role == "owner":
        raise RoomOwnerCannotLeaveException()

    await membership_repo.remove(db, id=membership.id)
    return "left"


async def delete_room(
    db: AsyncSession,
    room_id: int,
    user: User
):
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
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
    return "deleted"


async def toggle_room_ai(
    db: AsyncSession,
    room_id: int,
    ai_enabled: bool,
    user: User
):
    room = await room_repo.get(db, id=room_id)
    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
        raise RoomOwnerRequiredException("Only owner can update room")

    # Using update instead of directly modifying to exercise the repository
    await room_repo.update(
        db,
        db_obj=room,
        obj_in={"ai_enabled": ai_enabled}
    )
    return "updated"
