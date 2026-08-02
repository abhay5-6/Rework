from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.join_request import RoomJoinRequest
from app.models.membership import RoomMembership
from app.models.room import Room
from app.models.user import User
from app.core.exceptions import (
    AlreadyMemberException,
    JoinRequestNotFoundException,
    RoomJoinRequestPendingException,
    RoomOwnerRequiredException,
)


async def create_join_request(
    db: AsyncSession,
    room_id: int,
    user_id: int,
) -> str:
    existing_request_result = await db.execute(
        select(RoomJoinRequest).where(
            RoomJoinRequest.user_id == user_id,
            RoomJoinRequest.room_id == room_id,
            RoomJoinRequest.status == "pending",
        )
    )
    existing_request = existing_request_result.scalar()
    if existing_request:
        raise RoomJoinRequestPendingException()

    join_request = RoomJoinRequest(
        user_id=user_id,
        room_id=room_id,
        status="pending",
    )
    db.add(join_request)
    await db.commit()
    return "request_sent"


async def get_pending_requests(
    db: AsyncSession,
    current_user: User
):

    owner_memberships_result = (
        await db.execute(

            select(RoomMembership).where(
                RoomMembership.user_id
                    == current_user.id,

                RoomMembership.role
                    == "owner"
            )
        )
    )

    owner_memberships = (
        owner_memberships_result
        .scalars()
        .all()
    )

    owned_room_ids = [
        membership.room_id
        for membership
        in owner_memberships
    ]

    if not owned_room_ids:
        return []

    requests_result = await db.execute(

        select(
            RoomJoinRequest,
            Room,
            User
        )
        .join(
            Room,
            RoomJoinRequest.room_id
                == Room.id
        )
        .join(
            User,
            RoomJoinRequest.user_id
                == User.id
        )
        .where(
            RoomJoinRequest.room_id.in_(
                owned_room_ids
            ),

            RoomJoinRequest.status
                == "pending"
        )
    )

    requests = requests_result.all()

    formatted_requests = []

    for request, room, user in requests:

        formatted_requests.append({

            "request_id":
                request.id,

            "room_id":
                room.id,

            "room_name":
                room.name,

            "user_id":
                user.id,

            "username":
                user.username,

            "status":
                request.status
        })

    return formatted_requests


async def approve_join_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):

    request_result = await db.execute(

        select(RoomJoinRequest).where(
            RoomJoinRequest.id
                == request_id
        )
    )

    join_request = (
        request_result.scalar()
    )

    if not join_request:
        raise JoinRequestNotFoundException()

    membership_result = await db.execute(

        select(RoomMembership).where(

            RoomMembership.user_id
                == current_user.id,

            RoomMembership.room_id
                == join_request.room_id
        )
    )

    membership = (
        membership_result.scalar()
    )

    if (
        not membership
        or membership.role
            != "owner"
    ):

        raise RoomOwnerRequiredException("Not authorized")

    existing_member_result = (
        await db.execute(

            select(RoomMembership).where(

                RoomMembership.user_id
                    == join_request.user_id,

                RoomMembership.room_id
                    == join_request.room_id
            )
        )
    )

    existing_member = (
        existing_member_result.scalar()
    )

    if existing_member:

        raise AlreadyMemberException()

    new_membership = (
        RoomMembership(
            user_id=
                join_request.user_id,

            room_id=
                join_request.room_id,

            role="member"
        )
    )

    db.add(new_membership)

    join_request.status = (
        "approved"
    )

    await db.commit()

    return "approved"


async def reject_join_request(
    db: AsyncSession,
    request_id: int,
    current_user: User
):

    request_result = await db.execute(

        select(RoomJoinRequest).where(
            RoomJoinRequest.id
                == request_id
        )
    )

    join_request = (
        request_result.scalar()
    )

    if not join_request:
        raise JoinRequestNotFoundException()

    membership_result = await db.execute(

        select(RoomMembership).where(

            RoomMembership.user_id
                == current_user.id,

            RoomMembership.room_id
                == join_request.room_id
        )
    )

    membership = (
        membership_result.scalar()
    )

    if (
        not membership
        or membership.role
            != "owner"
    ):

        raise RoomOwnerRequiredException("Not authorized")

    join_request.status = (
        "rejected"
    )

    await db.commit()

    return "rejected"
