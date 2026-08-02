from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import RoomMembership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[RoomMembership, Dict[str, Any], Dict[str, Any]]):
    async def get_membership(self, db: AsyncSession, *, room_id: int, user_id: int) -> Optional[RoomMembership]:
        query = select(RoomMembership).where(
            RoomMembership.room_id == room_id,
            RoomMembership.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_room_members(self, db: AsyncSession, *, room_id: int) -> List[RoomMembership]:
        query = select(RoomMembership).where(RoomMembership.room_id == room_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_memberships(self, db: AsyncSession, *, user_id: int) -> List[RoomMembership]:
        query = select(RoomMembership).where(RoomMembership.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_memberships_by_role(self, db: AsyncSession, *, user_id: int, role: str) -> List[RoomMembership]:
        query = select(RoomMembership).where(
            RoomMembership.user_id == user_id,
            RoomMembership.role == role
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_room_members_with_users(self, db: AsyncSession, *, room_id: int):
        from app.models.user import User
        query = (
            select(RoomMembership, User)
            .join(User, RoomMembership.user_id == User.id)
            .where(RoomMembership.room_id == room_id)
        )
        result = await db.execute(query)
        return result.all()


membership_repo = MembershipRepository(RoomMembership)
