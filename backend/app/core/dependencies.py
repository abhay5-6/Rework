from fastapi import Depends, HTTPException
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
    tokenUrl="/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

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
