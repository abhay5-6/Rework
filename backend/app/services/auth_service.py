"""Password reset and email verification utilities"""

import secrets
import string
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.config import settings
from app.repositories.user_repository import user_repo


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def request_password_reset(
    db: AsyncSession,
    email: str
) -> str | None:
    """
    Generate a password reset token for a user.
    
    Returns:
        Reset token if user exists, None otherwise
    """
    user = await user_repo.get_by_email(db, email=email)

    if not user:
        return None

    # Generate reset token
    reset_token = generate_secure_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.password_reset_token_expire_hours
    )

    user.password_reset_token = reset_token
    user.password_reset_expires_at = expires_at

    await db.commit()
    return reset_token


async def validate_reset_token(
    db: AsyncSession,
    token: str
) -> User | None:
    """
    Validate a password reset token and return the user if valid.
    
    Returns:
        User if token is valid, None otherwise
    """
    user = await user_repo.get_by_reset_token(db, token=token)

    if not user:
        return None

    # Check if token has expired
    if user.password_reset_expires_at is None:
        return None

    if datetime.now(timezone.utc) > user.password_reset_expires_at:
        # Token expired
        user.password_reset_token = None
        user.password_reset_expires_at = None
        await db.commit()
        return None

    return user


async def generate_email_verification_token(
    db: AsyncSession,
    user_id: int
) -> str | None:
    """
    Generate an email verification token for a user.
    
    Returns:
        Verification token if user exists, None otherwise
    """
    user = await user_repo.get(db, id=user_id)

    if not user:
        return None

    if user.email_verified:
        return None

    verification_token = generate_secure_token()
    user.email_verification_token = verification_token

    await db.commit()
    return verification_token


async def verify_email_token(
    db: AsyncSession,
    token: str
) -> User | None:
    """
    Verify an email verification token and mark email as verified.
    
    Returns:
        User if token is valid, None otherwise
    """
    user = await user_repo.get_by_verification_token(db, token=token)

    if not user:
        return None

    if user.email_verified:
        return None

    user.email_verified = True
    user.email_verification_token = None

    await db.commit()
    return user
