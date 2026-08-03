from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room_memory import RoomMemory
from app.schemas.room_memory import RoomMemoryCreate, RoomMemoryUpdate
from app.repositories.base import BaseRepository

class MemoryRepository(BaseRepository[RoomMemory, RoomMemoryCreate, RoomMemoryUpdate]):
    async def get_memories_for_room(self, db: AsyncSession, *, room_id: int, skip: int = 0, limit: int = 50) -> List[RoomMemory]:
        query = (
            select(RoomMemory)
            .where(RoomMemory.room_id == room_id)
            .order_by(RoomMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_memories_for_room_with_users(self, db: AsyncSession, *, room_id: int, skip: int = 0, limit: int = 50):
        from app.models.user import User
        query = (
            select(RoomMemory, User.username)
            .outerjoin(User, RoomMemory.created_by == User.id)
            .where(RoomMemory.room_id == room_id)
            .order_by(RoomMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

    async def get_stale_memories(self, db: AsyncSession, *, room_id: int, threshold_date) -> List[RoomMemory]:
        query = select(RoomMemory).where(
            RoomMemory.room_id == room_id,
            RoomMemory.last_reinforced_at < threshold_date
        ).order_by(RoomMemory.last_reinforced_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_memory_in_room(self, db: AsyncSession, *, room_id: int, memory_id: int) -> Optional[RoomMemory]:
        query = select(RoomMemory).where(
            RoomMemory.id == memory_id,
            RoomMemory.room_id == room_id
        )
        result = await db.execute(query)
        return result.scalars().first()

memory_repo = MemoryRepository(RoomMemory)
