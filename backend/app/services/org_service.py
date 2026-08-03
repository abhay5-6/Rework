from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.organization import Organization, OrgMembership
from app.models.user import User
from app.schemas.org import OrgCreate
from app.repositories.org_repository import org_repo, org_membership_repo

async def create_organization(db: AsyncSession, org_in: OrgCreate, current_user_id: int) -> Organization:
    # Create the organization
    org = await org_repo.create(
        db, 
        obj_in={"name": org_in.name, "created_by": current_user_id}
    )

    # Add the creator as the owner
    await org_membership_repo.create(
        db,
        obj_in={"org_id": org.id, "user_id": current_user_id, "role": "owner"}
    )
    
    await db.refresh(org)
    return org

async def get_user_organizations(db: AsyncSession, user_id: int):
    # Depending on how order_by was handled, we can just return the list
    # The existing code did order_by(Organization.created_at.desc()), 
    # we might need to sort it manually or update the repository. 
    # For now, we sort manually.
    orgs = await org_repo.get_user_organizations(db, user_id=user_id)
    orgs.sort(key=lambda x: x.created_at, reverse=True)
    return orgs

async def get_organization(db: AsyncSession, org_id: int, user_id: int) -> Organization:
    # First verify membership
    membership = await org_membership_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    org = await org_repo.get(db, id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    return org

async def get_org_members(db: AsyncSession, org_id: int, user_id: int):
    # Verify membership
    membership = await org_membership_repo.get_membership(db, org_id=org_id, user_id=user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization"
        )

    result = await org_membership_repo.get_org_members_with_users(db, org_id=org_id)
    
    members = []
    for row in result:
        members.append({
            "org_id": org_id,
            "user_id": row.user_id,
            "role": row.role,
            "created_at": row.created_at,
            "username": row.username
        })
    return members

from app.schemas.org import OrgUpdate
async def update_organization(db: AsyncSession, org_id: int, org_in: OrgUpdate) -> Organization:
    org = await org_repo.get(db, id=org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
        
    update_data = org_in.model_dump(exclude_unset=True)
    org = await org_repo.update(db, db_obj=org, obj_in=update_data)
    return org
