from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.organization import Organization, OrgMembership
from app.schemas.org import OrgCreate
from app.repositories.base import BaseRepository


class OrgUpdate(BaseModel):
    name: Optional[str] = None


class OrgRepository(BaseRepository[Organization, OrgCreate, OrgUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Organization]:
        query = select(Organization).where(Organization.name == name)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_user_organizations(self, db: AsyncSession, *, user_id: int) -> List[Organization]:
        query = (
            select(Organization)
            .join(OrgMembership, Organization.id == OrgMembership.org_id)
            .where(OrgMembership.user_id == user_id)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


class OrgMembershipRepository(BaseRepository[OrgMembership, dict, dict]):
    async def get_membership(
        self, db: AsyncSession, *, org_id: int, user_id: int
    ) -> Optional[OrgMembership]:
        query = select(OrgMembership).where(
            OrgMembership.org_id == org_id,
            OrgMembership.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_org_members(self, db: AsyncSession, *, org_id: int) -> List[OrgMembership]:
        query = select(OrgMembership).where(OrgMembership.org_id == org_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_org_members_with_users(self, db: AsyncSession, *, org_id: int):
        from app.models.user import User
        query = (
            select(OrgMembership.user_id, OrgMembership.role, OrgMembership.created_at, User.username)
            .join(User, OrgMembership.user_id == User.id)
            .where(OrgMembership.org_id == org_id)
        )
        result = await db.execute(query)
        return result.all()


org_repo = OrgRepository(Organization)
org_membership_repo = OrgMembershipRepository(OrgMembership)
