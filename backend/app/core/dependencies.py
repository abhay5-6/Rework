from fastapi import Depends, HTTPException, Request
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
    
    Args:
        request: The incoming FastAPI HTTP Request.
        token: The Bearer token extracted from the Authorization header (if present).
        db: Database session dependency.
        
    Returns:
        The authenticated User model instance.
        
    Raises:
        HTTPException 401: If credentials are missing, invalid, or user does not exist.
        HTTPException 403: If CSRF verification fails when using cookie authentication.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    auth_token = None
    is_cookie_auth = False

    # 1. Check HttpOnly cookie
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
                status_code=403,
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



async def get_arq_pool(request: Request):
    """Dependency to get the ARQ queue pool from app state."""
    return getattr(request.app.state, "arq_pool", None)
