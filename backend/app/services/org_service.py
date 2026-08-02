from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.models.organization import Organization, OrgMembership
from app.models.user import User
from app.schemas.org import OrgCreate

async def create_organization(db: AsyncSession, org_in: OrgCreate, current_user_id: int) -> Organization:
    # Create the organization
    org = Organization(name=org_in.name, created_by=current_user_id)
    db.add(org)
    await db.flush()

    # Add the creator as the owner
    membership = OrgMembership(org_id=org.id, user_id=current_user_id, role="owner")
    db.add(membership)
    await db.commit()
    await db.refresh(org)

    return org

async def get_user_organizations(db: AsyncSession, user_id: int):
    stmt = (
        select(Organization)
        .join(OrgMembership, Organization.id == OrgMembership.org_id)
        .where(OrgMembership.user_id == user_id)
        .order_by(Organization.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_organization(db: AsyncSession, org_id: int, user_id: int) -> Organization:
    # First verify membership
    membership_stmt = select(OrgMembership).where(
        OrgMembership.org_id == org_id,
        OrgMembership.user_id == user_id
    )
    membership_result = await db.execute(membership_stmt)
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return org

async def get_org_members(db: AsyncSession, org_id: int, user_id: int):
    # Verify membership
    membership_stmt = select(OrgMembership).where(
        OrgMembership.org_id == org_id,
        OrgMembership.user_id == user_id
    )
    membership_result = await db.execute(membership_stmt)
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    stmt = (
        select(OrgMembership.user_id, OrgMembership.role, OrgMembership.created_at, User.username)
        .join(User, OrgMembership.user_id == User.id)
        .where(OrgMembership.org_id == org_id)
    )
    result = await db.execute(stmt)
    
    members = []
    for row in result.all():
        members.append({
            "org_id": org_id,
            "user_id": row.user_id,
            "role": row.role,
            "created_at": row.created_at,
            "username": row.username
        })
    return members
