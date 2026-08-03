from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.membership import (
    WorkspaceMembership
)
from app.models.user import User


async def get_membership(
    db: AsyncSession,
    workspace_id: int,
    user_id: int
):

    result = await db.execute(

        select(WorkspaceMembership)
        .where(
            WorkspaceMembership.workspace_id
                == workspace_id,

            WorkspaceMembership.user_id
                == user_id
        )
    )

    return result.scalar_one_or_none()


def is_owner(
    membership: WorkspaceMembership | None
) -> bool:
    """Check if user is workspace owner"""
    return (
        membership is not None
        and membership.role == "owner"
    )


def is_workspace_owner(
    membership: WorkspaceMembership | None
):
    """Alias for is_owner - for backward compatibility"""
    return is_owner(membership)


def is_admin(
    membership: WorkspaceMembership | None
) -> bool:
    """Check if user is workspace admin or owner"""
    return (
        membership is not None
        and membership.role in [
            "owner",
            "admin"
        ]
    )


def is_workspace_admin(
    membership: WorkspaceMembership | None
):
    """Alias for is_admin - for backward compatibility"""
    return is_admin(membership)


def can_manage_workspace(
    membership: WorkspaceMembership | None
):

    return is_workspace_admin(
        membership
    )


async def require_workspace_owner(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceMembership:
    membership = await get_membership(db, workspace_id, current_user.id)
    if not is_owner(membership):
        raise HTTPException(
            status_code=403,
            detail="Only owner can perform this action",
        )
    return membership


async def require_workspace_admin(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceMembership:
    membership = await get_membership(db, workspace_id, current_user.id)
    if not is_admin(membership):
        raise HTTPException(
            status_code=403,
            detail="Not authorized",
        )
    return membership