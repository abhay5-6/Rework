from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenDecodeError,
    decode_access_token
)
from app.db.session import get_db
from app.models.user import User

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


async def get_arq_pool(request: Request):
    """Dependency to get the ARQ queue pool from app state."""
    return getattr(request.app.state, "arq_pool", None)
