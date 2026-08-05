import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.database import Base, DATABASE_URL
from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password

# Use NullPool for tests so asyncpg allocates a clean connection per AsyncSession task
test_engine = create_async_engine(DATABASE_URL, poolclass=NullPool)



@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a dedicated AsyncSession for setting up test data."""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provides an AsyncClient for sending HTTP requests to the FastAPI application."""
    async def override_get_db():
        async with AsyncSession(test_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Fixture creating a standard verified test user."""
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "testuser@example.com"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
        email_verified=True,
        is_system_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    """Fixture creating an admin test user."""
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "adminuser@example.com"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    user = User(
        username="adminuser",
        email="adminuser@example.com",
        hashed_password=hash_password("password123"),
        email_verified=True,
        is_system_admin=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

