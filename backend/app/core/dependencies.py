import logging
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    decode_access_token,
    verify_csrf_token
)
from app.db.session import get_db
from app.models.user import User
from app.models.organization import OrgMembership


from app.models.workspace import Workspace
from app.models.membership import WorkspaceMembership, ChannelMembership

from app.models.channel import Channel


logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to authenticate a user. Supports:
    1. HttpOnly access_token_cookie with double-submit CSRF token validation for state-changing HTTP requests.
    2. Authorization: Bearer <token> header fallback for API clients and backward compatibility.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    auth_token = None
    is_cookie_auth = False

    # 1. Check HttpOnly cookie first
    cookie_token = request.cookies.get("access_token_cookie")
    if cookie_token:
        auth_token = cookie_token
        is_cookie_auth = True
    elif token:
        auth_token = token

    if not auth_token:
        raise credentials_exception

    # 2. CSRF check for state-changing requests when authenticated via cookie
    if is_cookie_auth and request.method in ("POST", "PUT", "DELETE", "PATCH"):
        csrf_header = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")
        if not verify_csrf_token(csrf_header, csrf_cookie):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )

    try:
        payload = decode_access_token(auth_token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except TokenDecodeError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar()

    if user is None:
        raise credentials_exception

    return user


async def require_system_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency verifying that current user has system administrator privileges."""
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System administrator privileges required"
        )
    return current_user


async def verify_org_access(
    db: AsyncSession,
    org_id: int,
    user: User,
    require_admin: bool = False
) -> OrgMembership:
    """Centralized verification for Organization membership and admin roles."""
    stmt = select(OrgMembership).where(
        OrgMembership.org_id == org_id,
        OrgMembership.user_id == user.id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )

    if require_admin and member.role not in ("admin", "owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin privileges required"
        )

    return member



async def verify_workspace_access(
    db: AsyncSession,
    workspace_id: int,
    user: User,
    require_admin: bool = False
) -> WorkspaceMembership:
    """Centralized verification for Workspace membership and privacy controls."""
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws_res = await db.execute(ws_stmt)
    ws = ws_res.scalar_one_or_none()

    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    mem_stmt = select(WorkspaceMembership).where(
        WorkspaceMembership.workspace_id == workspace_id,
        WorkspaceMembership.user_id == user.id
    )
    mem_res = await db.execute(mem_stmt)
    membership = mem_res.scalar_one_or_none()

    if not membership:
        if ws.is_private and not user.is_system_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )
        # If public workspace and not a member, check org level access
        if ws.organization_id:
            await verify_org_access(db, ws.organization_id, user)

    if require_admin:
        if not membership or membership.role not in ("admin", "owner"):
            if not user.is_system_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace admin privileges required"
                )

    return membership


async def verify_channel_access(
    db: AsyncSession,
    channel_id: int,
    user: User
) -> Channel:
    """Centralized verification for Channel access and privacy rules."""
    ch_stmt = select(Channel).where(Channel.id == channel_id)
    ch_res = await db.execute(ch_stmt)
    channel = ch_res.scalar_one_or_none()

    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Channel not found"
        )

    await verify_workspace_access(db, channel.workspace_id, user)

    if channel.is_private and not user.is_system_admin:
        cm_stmt = select(ChannelMembership).where(
            ChannelMembership.channel_id == channel_id,
            ChannelMembership.user_id == user.id
        )
        cm_res = await db.execute(cm_stmt)
        channel_member = cm_res.scalar_one_or_none()

        if not channel_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this private channel"
            )

    return channel


async def get_arq_pool(request: Request):
    """Dependency to get the ARQ queue pool from app state."""
    return getattr(request.app.state, "arq_pool", None)
