from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    decode_access_token
)
from app.models.user import User
from app.models.workspace import Workspace

from app.models.membership import (
    WorkspaceMembership
)


async def authenticate_websocket(
    token: str,
    workspace_id: int,
    db: AsyncSession
):

    try:

        payload = decode_access_token(
            token
        )

        email = payload.get("sub")

        if not email:
            return None

    except TokenDecodeError:
        return None

    user_result = await db.execute(
        select(User).where(
            User.email == email
        )
    )

    user = user_result.scalar()

    if not user:
        return None

    workspace_result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id
        )
    )

    workspace = workspace_result.scalar()

    if not workspace:
        return None

    # PUBLIC WORKSPACE
    if not workspace.is_private:
        return user

    # PRIVATE WORKSPACE

    membership_result = await db.execute(
        select(WorkspaceMembership).where(
            WorkspaceMembership.user_id == user.id,
            WorkspaceMembership.workspace_id == workspace_id
        )
    )

    membership = membership_result.scalar()

    if not membership:
        return None

    return user
