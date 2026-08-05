from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.core.security import verify_password
from app.core.exceptions import (
    EmailAlreadyRegisteredException,
    UsernameAlreadyTakenException,
)
from app.repositories.user_repository import user_repo


async def create_user(
    db: AsyncSession,
    user_data: UserCreate
):
    existing_email = await user_repo.get_by_email(db, email=user_data.email)
    if existing_email:
        raise EmailAlreadyRegisteredException()
        
    existing_username = await user_repo.get_by_username(db, username=user_data.username)
    if existing_username:
        raise UsernameAlreadyTakenException()

    user_data_hashed = user_data.model_dump()
    user_data_hashed["hashed_password"] = hash_password(user_data_hashed.pop("password"))
    
    import secrets
    from app.core.config import settings
    token = secrets.token_urlsafe(32)
    user_data_hashed["email_verification_token"] = token
    user_data_hashed["email_verified"] = not settings.email_verification_enabled
    
    new_user = await user_repo.create(db, obj_in=user_data_hashed)
    
    if settings.email_verification_enabled:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"VERIFICATION LINK FOR {new_user.email}: {settings.frontend_url}/verify-email?token={token}")
        
    return new_user

async def authenticate_user(
    db: AsyncSession,
    email_or_username: str,
    password: str
):
    user = await user_repo.get_by_email(db, email=email_or_username)
    if not user:
        user = await user_repo.get_by_username(db, username=email_or_username)

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password
    ):
        return None

    return user