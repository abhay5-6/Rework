from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.membership import (
    RoomMembership
)

from app.models.user import User

from app.models.room import Room
from app.utils.permissions import (
    get_membership,
    is_room_owner,
    is_room_admin
)


async def get_room_members(
    db: AsyncSession,
    room_id: int,
    current_user: User
):

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

        allowed = True

    else:

        membership_check = await db.execute(

            select(RoomMembership).where(

                RoomMembership.room_id
                    == room_id,

                RoomMembership.user_id
                    == current_user.id
            )
        )

        allowed = (
            membership_check.scalar()
            is not None
        )

    if not allowed:

        return None

    result = await db.execute(

        select(
            RoomMembership,
            User
        )
        .join(
            User,
            RoomMembership.user_id
                == User.id
        )
        .where(
            RoomMembership.room_id
                == room_id
        )
    )

    members = result.all()

    formatted_members = []

    for membership, user in members:

        formatted_members.append({

            "user_id":
                user.id,

            "username":
                user.username,

            "role":
                membership.role
        })

    return formatted_members


async def promote_member(
    db: AsyncSession,
    room_id: int,
    target_user_id: int,
    current_user: User
):

    current_membership = (
        await get_membership(
            db,
            room_id,
            current_user.id
        )
    )

    if not is_room_owner(
        current_membership
    ):

        return "not_owner"

    target_membership = (
        await get_membership(
            db,
            room_id,
            target_user_id
        )
    )

    if not target_membership:

        return "member_not_found"

    if target_membership.role == "owner":

        return "cannot_modify_owner"

    if target_membership.role == "admin":

        return "already_admin"

    target_membership.role = "admin"

    await db.commit()

    return "promoted"


async def demote_member(
    db: AsyncSession,
    room_id: int,
    target_user_id: int,
    current_user: User
):

    current_membership = (
        await get_membership(
            db,
            room_id,
            current_user.id
        )
    )

    if not is_room_owner(
        current_membership
    ):

        return "not_owner"

    if target_user_id == current_user.id:

        return "cannot_demote_self"

    target_membership = (
        await get_membership(
            db,
            room_id,
            target_user_id
        )
    )

    if not target_membership:

        return "member_not_found"

    if target_membership.role == "owner":

        return "cannot_modify_owner"

    if target_membership.role == "member":

        return "already_member"

    target_membership.role = "member"

    await db.commit()

    return "demoted"


async def remove_member(
    db: AsyncSession,
    room_id: int,
    target_user_id: int,
    current_user: User
):

    current_membership = (
        await get_membership(
            db,
            room_id,
            current_user.id
        )
    )

    if not is_room_admin(
        current_membership
    ):

        return "not_authorized"

    if target_user_id == current_user.id:

        return "cannot_remove_self"

    target_membership = (
        await get_membership(
            db,
            room_id,
            target_user_id
        )
    )

    if not target_membership:

        return "member_not_found"

    if target_membership.role == "owner":

        return "cannot_remove_owner"

    if (
        current_membership.role == "admin"
        and target_membership.role == "admin"
    ):

        return "cannot_remove_admin"

    await db.delete(
        target_membership
    )

    await db.commit()

    return "removed"
