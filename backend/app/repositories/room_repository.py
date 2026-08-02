from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room, RoomCreate, RoomUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Room]:
        query = select(Room).where(Room.name == name)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_public_rooms(self, db: AsyncSession) -> List[Room]:
        query = select(Room).where(Room.is_private == False)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_rooms_count(self, db: AsyncSession, *, organization_id: Optional[int] = None) -> int:
        query = select(Room)
        if organization_id is not None:
            query = query.where(Room.organization_id == organization_id)
        result = await db.execute(query)
        return len(result.scalars().all())

    async def get_paginated_rooms(
        self, db: AsyncSession, *, organization_id: Optional[int] = None, skip: int = 0, limit: int = 10
    ) -> List[Room]:
        query = select(Room)
        if organization_id is not None:
            query = query.where(Room.organization_id == organization_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


room_repo = RoomRepository(Room)
