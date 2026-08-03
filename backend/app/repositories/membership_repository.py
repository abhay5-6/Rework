from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import WorkspaceMembership
from app.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[WorkspaceMembership, Dict[str, Any], Dict[str, Any]]):
    async def get_membership(self, db: AsyncSession, *, workspace_id: int, user_id: int) -> Optional[WorkspaceMembership]:
        query = select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_workspace_members(self, db: AsyncSession, *, workspace_id: int) -> List[WorkspaceMembership]:
        query = select(WorkspaceMembership).where(WorkspaceMembership.workspace_id == workspace_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_memberships(self, db: AsyncSession, *, user_id: int) -> List[WorkspaceMembership]:
        query = select(WorkspaceMembership).where(WorkspaceMembership.user_id == user_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_memberships_by_role(self, db: AsyncSession, *, user_id: int, role: str) -> List[WorkspaceMembership]:
        query = select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user_id,
            WorkspaceMembership.role == role
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_workspace_members_with_users(self, db: AsyncSession, *, workspace_id: int):
        from app.models.user import User
        query = (
            select(WorkspaceMembership, User)
            .join(User, WorkspaceMembership.user_id == User.id)
            .where(WorkspaceMembership.workspace_id == workspace_id)
        )
        result = await db.execute(query)
        return result.all()


membership_repo = MembershipRepository(WorkspaceMembership)
