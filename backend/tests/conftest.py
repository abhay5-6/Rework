import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, engine as global_engine
from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password

# For tests, we use the same database but wrap every test in a transaction that is rolled back.

@pytest_asyncio.fixture(scope="function")
async def db_session():
    # Connect to the database
    async with global_engine.connect() as conn:
        # Start a transaction
        transaction = await conn.begin()
        # Bind an AsyncSession to this connection
        async_session = AsyncSession(
            bind=conn, 
            expire_on_commit=False,
            join_transaction_mode="create_savepoint"
        )
        
        try:
            yield async_session
        finally:
            await async_session.close()
            # Rollback the transaction to keep db clean
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    user = User(
        username="testuser",
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
        email_verified=True,
        is_system_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    user = User(
        username="adminuser",
        email="adminuser@example.com",
        hashed_password=hash_password("password123"),
        email_verified=True,
        is_system_admin=True
    )
    db_session.add(user)
    await db_session.commit()
    return user
