from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    decode_access_token,
    decode_websocket_ticket
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
    """
    Authenticates a WebSocket connection using either a short-lived WebSocket ticket or a standard access token/cookie.
    Validates workspace membership permissions.
    """
    email = None

    # 1. Try single-use short-lived WebSocket ticket first
    try:
        payload = decode_websocket_ticket(token)
        if payload.get("workspace_id") == workspace_id:
            email = payload.get("sub")
    except TokenDecodeError:
        pass

    # 2. Fallback to standard access token
    if not email:
        try:
            payload = decode_access_token(token)
            email = payload.get("sub")
        except TokenDecodeError:
            return None

    if not email:
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
