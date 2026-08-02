from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.models.desk import Desk
from app.schemas.room import RoomCreate

from app.models.membership import RoomMembership
from app.models.organization import OrgMembership
from app.models.user import User
from app.models.message import Message

from app.models.join_request import (
    RoomJoinRequest
)
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
        org_mem = await db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == room_data.organization_id,
                OrgMembership.user_id == creator.id
            )
        )
        if not org_mem.scalar_one_or_none():
            raise RoomAlreadyExistsException()

    query = select(Room).where(Room.name == room_data.name)
    if room_data.organization_id is not None:
        query = query.where(Room.organization_id == room_data.organization_id)
        
    existing_room = await db.execute(query)

    if existing_room.scalar():
        raise RoomAlreadyExistsException()

    room = Room(
        name=room_data.name,
        description=room_data.description,
        is_private=room_data.is_private,
        ai_enabled=room_data.ai_enabled,
        organization_id=room_data.organization_id,
        owner_id=creator.id
    )

    db.add(room)

    await db.flush()

    membership = RoomMembership(
        user_id=creator.id,
        room_id=room.id,
        role="owner"
    )

    db.add(membership)

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
        org_mem = await db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == organization_id,
                OrgMembership.user_id == current_user.id
            )
        )
        if not org_mem.scalar_one_or_none():
            return {"items": [], "total": 0}

    # Get total count of rooms
    count_stmt = select(Room)
    if organization_id is not None:
        count_stmt = count_stmt.where(Room.organization_id == organization_id)
    count_result = await db.execute(count_stmt)
    total_rooms = len(count_result.scalars().all())

    # Fetch paginated rooms
    stmt = select(Room)
    if organization_id is not None:
        stmt = stmt.where(Room.organization_id == organization_id)
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)

    rooms = result.scalars().all()

    # Fetch all memberships for current user in one query
    memberships_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.user_id == current_user.id
        )
    )

    memberships = memberships_result.scalars().all()
    
    # Fetch all pending join requests for current user in one query
    requests_result = await db.execute(
        select(RoomJoinRequest).where(
            RoomJoinRequest.user_id == current_user.id,
            RoomJoinRequest.status == "pending"
        )
    )

    pending_requests = requests_result.scalars().all()

    # Build maps for fast lookup
    membership_map = {
        m.room_id: m 
        for m in memberships
    }
    
    pending_request_map = {
        r.room_id: r 
        for r in pending_requests
    }

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
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar()
    
    if not room:
        return None

    membership_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.user_id == current_user.id,
            RoomMembership.room_id == room_id
        )
    )
    membership = membership_result.scalar()

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

    room_result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    room = room_result.scalar()

    if not room:

        raise RoomNotFoundException()

    membership_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.user_id == user.id,
            RoomMembership.room_id == room_id
        )
    )

    existing_membership = (
        membership_result.scalar()
    )

    if existing_membership:

        raise RoomAlreadyJoinedException()

    # PUBLIC ROOM
    if not room.is_private:

        membership = RoomMembership(
            user_id=user.id,
            room_id=room_id,
            role="member"
        )

        db.add(membership)

        await db.commit()

        await db.refresh(membership)

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

    room_result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    room = room_result.scalar()

    if not room:
        raise RoomNotFoundException()

    membership_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.user_id == user.id,
            RoomMembership.room_id == room_id
        )
    )

    membership = membership_result.scalar()

    if not membership:
        raise RoomMembershipRequiredException()

    if membership.role == "owner":
        raise RoomOwnerCannotLeaveException()

    await db.delete(membership)

    await db.commit()

    return "left"


async def delete_room(
    db: AsyncSession,
    room_id: int,
    user: User
):

    room_result = await db.execute(
        select(Room).where(
            Room.id == room_id
        )
    )

    room = room_result.scalar()

    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
        raise RoomOwnerRequiredException("Only owner can delete room")

    memberships_result = await db.execute(
        select(RoomMembership).where(
            RoomMembership.room_id == room_id
        )
    )

    memberships = (
        memberships_result.scalars().all()
    )

    for membership in memberships:

        await db.delete(membership)

    messages_result = await db.execute(
        select(Message).where(
            Message.room_id == room_id
        )
    )

    messages = (
        messages_result.scalars().all()
    )

    for message in messages:

        await db.delete(message)

    await db.delete(room)

    await db.commit()

    return "deleted"

async def toggle_room_ai(
    db: AsyncSession,
    room_id: int,
    ai_enabled: bool,
    user: User
):
    room_result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = room_result.scalar()

    if not room:
        raise RoomNotFoundException()

    if room.owner_id != user.id:
        raise RoomOwnerRequiredException("Only owner can update room")

    room.ai_enabled = ai_enabled
    await db.commit()
    return "updated"
