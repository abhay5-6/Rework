from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.join_request import RoomJoinRequest
from app.repositories.base import BaseRepository


class JoinRequestRepository(BaseRepository[RoomJoinRequest, Dict[str, Any], Dict[str, Any]]):
    async def get_join_request(self, db: AsyncSession, *, room_id: int, user_id: int) -> Optional[RoomJoinRequest]:
        query = select(RoomJoinRequest).where(
            RoomJoinRequest.room_id == room_id,
            RoomJoinRequest.user_id == user_id,
            RoomJoinRequest.status == "pending"
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_room_requests(self, db: AsyncSession, *, room_id: int) -> List[RoomJoinRequest]:
        query = select(RoomJoinRequest).where(
            RoomJoinRequest.room_id == room_id,
            RoomJoinRequest.status == "pending"
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_pending_requests_with_details(self, db: AsyncSession, *, owned_room_ids: List[int]):
        from app.models.room import Room
        from app.models.user import User
        query = (
            select(RoomJoinRequest, Room, User)
            .join(Room, RoomJoinRequest.room_id == Room.id)
            .join(User, RoomJoinRequest.user_id == User.id)
            .where(
                RoomJoinRequest.room_id.in_(owned_room_ids),
                RoomJoinRequest.status == "pending"
            )
        )
        result = await db.execute(query)
        return result.all()


join_request_repo = JoinRequestRepository(RoomJoinRequest)
