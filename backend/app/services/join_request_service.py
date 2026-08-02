from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.exceptions import (
    AlreadyMemberException,
    JoinRequestNotFoundException,
    RoomJoinRequestPendingException,
    RoomOwnerRequiredException,
)
from app.repositories.join_request_repository import join_request_repo
from app.repositories.membership_repository import membership_repo


async def create_join_request(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> str:
    existing_request = await join_request_repo.get_join_request(db, room_id=room_id, user_id=user_id)
    if existing_request:
        raise RoomJoinRequestPendingException()

    await join_request_repo.create(
        db,
        obj_in={
            "user_id": user_id,
            "room_id": room_id,
            "status": "pending"
        }
    )
    return "request_sent"


async def get_pending_requests(
    db: AsyncSession,
    current_user: User
):
    owner_memberships = await membership_repo.get_user_memberships_by_role(db, user_id=current_user.id, role="owner")
    owned_room_ids = [m.room_id for m in owner_memberships]

    if not owned_room_ids:
        return []

    requests = await join_request_repo.get_pending_requests_with_details(db, owned_room_ids=owned_room_ids)

    formatted_requests = []
    for request, room, user in requests:
        formatted_requests.append({
            "request_id": request.id,
            "room_id": room.id,
            "room_name": room.name,
            "user_id": user.id,
            "username": user.username,
            "status": request.status
        })

    return formatted_requests


async def approve_join_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):
    join_request = await join_request_repo.get(db, id=request_id)
    if not join_request:
        raise JoinRequestNotFoundException()

    membership = await membership_repo.get_membership(db, room_id=join_request.room_id, user_id=current_user.id)
    if not membership or membership.role != "owner":
        raise RoomOwnerRequiredException("Not authorized")

    existing_member = await membership_repo.get_membership(db, room_id=join_request.room_id, user_id=join_request.user_id)
    if existing_member:
        raise AlreadyMemberException()

    await membership_repo.create(
        db,
        obj_in={
            "user_id": join_request.user_id,
            "room_id": join_request.room_id,
            "role": "member"
        }
    )

    join_request.status = "approved"
    await db.commit()
    return "approved"


async def reject_join_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):
    join_request = await join_request_repo.get(db, id=request_id)
    if not join_request:
        raise JoinRequestNotFoundException()

    membership = await membership_repo.get_membership(db, room_id=join_request.room_id, user_id=current_user.id)
    if not membership or membership.role != "owner":
        raise RoomOwnerRequiredException("Not authorized")

    join_request.status = "rejected"
    await db.commit()
    return "rejected"

