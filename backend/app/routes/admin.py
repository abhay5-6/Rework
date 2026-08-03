from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.utils.permissions import require_system_admin

router = APIRouter()

@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_system_admin)
):
    users_count = await db.scalar(select(func.count()).select_from(User))
    orgs_count = await db.scalar(select(func.count()).select_from(Organization))
    workspaces_count = await db.scalar(select(func.count()).select_from(Workspace))

    return {
        "users": users_count,
        "organizations": orgs_count,
        "workspaces": workspaces_count
    }
