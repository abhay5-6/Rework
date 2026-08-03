from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.membership import (
    WorkspaceMembership
)


async def get_membership(
    db: AsyncSession,
    workspace_id: int,
    user_id: int
):

    result = await db.execute(

        select(WorkspaceMembership).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.user_id == user_id
        )
    )

    return result.scalar_one_or_none()