from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.membership import (
    RoomMembership
)
from app.models.user import User


async def get_membership(
    db: AsyncSession,
    room_id: int,
    user_id: int
):

    result = await db.execute(

        select(RoomMembership)
        .where(
            RoomMembership.room_id
                == room_id,

            RoomMembership.user_id
                == user_id
        )
    )

    return result.scalar_one_or_none()


def is_owner(
    membership: RoomMembership | None
) -> bool:
    """Check if user is room owner"""
    return (
        membership is not None
        and membership.role == "owner"
    )


def is_room_owner(
    membership: RoomMembership | None
):
    """Alias for is_owner - for backward compatibility"""
    return is_owner(membership)


def is_admin(
    membership: RoomMembership | None
) -> bool:
    """Check if user is room admin or owner"""
    return (
        membership is not None
        and membership.role in [
            "owner",
            "admin"
        ]
    )


def is_room_admin(
    membership: RoomMembership | None
):
    """Alias for is_admin - for backward compatibility"""
    return is_admin(membership)


def can_manage_room(
    membership: RoomMembership | None
):

    return is_room_admin(
        membership
    )


async def require_room_owner(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomMembership:
    membership = await get_membership(db, room_id, current_user.id)
    if not is_owner(membership):
        raise HTTPException(
            status_code=403,
            detail="Only owner can perform this action",
        )
    return membership


async def require_room_admin(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomMembership:
    membership = await get_membership(db, room_id, current_user.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )
    return membership