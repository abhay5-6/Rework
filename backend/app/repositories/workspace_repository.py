from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.workspace import Workspace
from app.schemas.workspace import RoomCreate, RoomUpdate
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Workspace, RoomCreate, RoomUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.name == name)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_public_workspaces(self, db: AsyncSession) -> List[Workspace]:
        query = select(Workspace).where(Workspace.is_private == False)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_workspaces_count(self, db: AsyncSession, *, organization_id: Optional[int] = None) -> int:
        query = select(Workspace)
        if organization_id is not None:
            query = query.where(Workspace.organization_id == organization_id)
        result = await db.execute(query)
        return len(result.scalars().all())

    async def get_paginated_workspaces(
        self, db: AsyncSession, *, organization_id: Optional[int] = None, skip: int = 0, limit: int = 10
    ) -> List[Workspace]:
        query = select(Workspace)
        if organization_id is not None:
            query = query.where(Workspace.organization_id == organization_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())


workspace_repo = RoomRepository(Workspace)
