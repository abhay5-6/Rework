from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.org import OrganizationSchema, OrgCreate, OrgMemberSchema, OrgMemberAdd
from app.services import org_service
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
from app.schemas.org import OrgUpdate

@router.patch("/{org_id}", response_model=OrganizationSchema)
async def update_org(
    org_id: int,
    org_in: OrgUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.utils.permissions import require_org_admin
    await require_org_admin(org_id, db, current_user)
    return await org_service.update_organization(db, org_id, org_in)

@router.post("/", response_model=OrganizationSchema)
async def create_org(
    org_in: OrgCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await org_service.create_organization(db, org_in, current_user.id)

@router.get("/", response_model=List[OrganizationSchema])
async def get_my_orgs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await org_service.get_user_organizations(db, current_user.id)

@router.get("/{org_id}", response_model=OrganizationSchema)
async def get_org(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await org_service.get_organization(db, org_id, current_user.id)

@router.get("/{org_id}/members", response_model=List[OrgMemberSchema])
async def get_org_members(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await org_service.get_org_members(db, org_id, current_user.id)
