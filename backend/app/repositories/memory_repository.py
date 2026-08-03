from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace_memory import WorkspaceMemory
from app.schemas.workspace_memory import WorkspaceMemoryCreate, WorkspaceMemoryUpdate
from app.repositories.base import BaseRepository

class MemoryRepository(BaseRepository[WorkspaceMemory, WorkspaceMemoryCreate, WorkspaceMemoryUpdate]):
    async def get_memories_for_workspace(self, db: AsyncSession, *, workspace_id: int, skip: int = 0, limit: int = 50) -> List[WorkspaceMemory]:
        query = (
            select(WorkspaceMemory)
            .where(WorkspaceMemory.workspace_id == workspace_id)
            .order_by(WorkspaceMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_memories_for_workspace_with_users(self, db: AsyncSession, *, workspace_id: int, skip: int = 0, limit: int = 50):
        from app.models.user import User
        query = (
            select(WorkspaceMemory, User.username)
            .outerjoin(User, WorkspaceMemory.created_by == User.id)
            .where(WorkspaceMemory.workspace_id == workspace_id)
            .order_by(WorkspaceMemory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

    async def get_stale_memories(self, db: AsyncSession, *, workspace_id: int, threshold_date) -> List[WorkspaceMemory]:
        query = select(WorkspaceMemory).where(
            WorkspaceMemory.workspace_id == workspace_id,
            WorkspaceMemory.last_reinforced_at < threshold_date
        ).order_by(WorkspaceMemory.last_reinforced_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_memory_in_workspace(self, db: AsyncSession, *, workspace_id: int, memory_id: int) -> Optional[WorkspaceMemory]:
        query = select(WorkspaceMemory).where(
            WorkspaceMemory.id == memory_id,
            WorkspaceMemory.workspace_id == workspace_id
        )
        result = await db.execute(query)
        return result.scalars().first()

memory_repo = MemoryRepository(WorkspaceMemory)
