from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.user import User
from app.schemas.user import UserCreate
from app.repositories.base import BaseRepository


class UserUpdate(BaseModel):
    # Will be populated as needed
    pass


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_reset_token(self, db: AsyncSession, *, token: str) -> Optional[User]:
        query = select(User).where(User.password_reset_token == token)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_verification_token(self, db: AsyncSession, *, token: str) -> Optional[User]:
        query = select(User).where(User.email_verification_token == token)
        result = await db.execute(query)
        return result.scalars().first()


user_repo = UserRepository(User)
