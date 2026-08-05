from fastapi import Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.security import (
    TokenDecodeError,
    decode_access_token
)
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to authenticate a user using an OAuth2 Bearer token in the HTTP Authorization header.
    
    Args:
        token: The Bearer token extracted from the Authorization header.
        db: Database session dependency.
        
    Returns:
        The authenticated User model instance.
        
    Raises:
        HTTPException 401: If the token is missing, invalid, or user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(
            token
        )

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


async def get_current_user_from_header_or_param(
    request: Request,
    token_param: str | None = Query(None, alias="token"),
    header_token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to authenticate a user using either an Authorization header or a 'token' query parameter.
    This enables secure file downloads for media tags (e.g. <img> or <video>) that cannot supply custom headers.
    
    Args:
        request: The incoming HTTP request.
        token_param: Optional token supplied via ?token= query parameter.
        header_token: Optional token supplied via Authorization Bearer header.
        db: Database session dependency.
        
    Returns:
        The authenticated User model instance.
        
    Raises:
        HTTPException 401: If neither token source is valid or user is not found.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    raw_token = header_token or token_param
    if not raw_token:
        logger.warning("Authentication failed: No token provided in header or query parameter", extra={"path": request.url.path})
        raise credentials_exception

    try:
        payload = decode_access_token(raw_token)
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except TokenDecodeError:
        logger.warning("Authentication failed: Invalid token format", extra={"path": request.url.path})
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalar()

    if user is None:
        logger.warning("Authentication failed: User not found for token email", extra={"email": email})
        raise credentials_exception

    return user


async def get_arq_pool(request: Request):
    """Dependency to get the ARQ queue pool from app state."""
    return getattr(request.app.state, "arq_pool", None)
