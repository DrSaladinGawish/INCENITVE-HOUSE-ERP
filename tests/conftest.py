"""Pytest configuration — async test fixtures with SQLite in-memory."""

import pytest
import asyncio
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, AsyncSessionLocal
from app.models.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite://"

# Single engine + session factory shared across all overrides
_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_test_session_factory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await _test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _test_session_factory() as session:
        yield session


async def override_get_db():
    async with _test_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


MOCK_USER = {"username": "admin", "role": "admin"}


async def override_get_current_user():
    return MOCK_USER


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    from app.routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
