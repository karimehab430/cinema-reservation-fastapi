import asyncio
import pytest
from httpx import AsyncClient
from redis import asyncio as aioredis
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.cache import Cache
from app.core.config import settings
from app.main import app
from app.db import session as db_session_module
from app.db.session import Base
from app.dependencies import get_db
from app.models import Cinema


class InMemoryCacheBackend:
    def __init__(self):
        self._store = {}

    async def get(self, key: str):
        return self._store.get(key)

    async def set(self, key: str, value, ttl_seconds: int | None = None):
        self._store[key] = value

    async def delete(self, key: str):
        self._store.pop(key, None)

    async def delete_pattern(self, pattern: str):
        keys_to_delete = [key for key in self._store if key.startswith(pattern)]
        for key in keys_to_delete:
            self._store.pop(key, None)



TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_database.db"


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        future=True,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="session")
def session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(session_maker):
    async with session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def reset_database(engine):
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def redis_client():
    return settings.redis_url


@pytest.fixture(autouse=True)
async def override_get_db(session_maker):
    async def _get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_cinemas_returns_empty_when_no_cinemas():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/v1/cinemas")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_create_cinema_returns_201():
    payload = {"name": "New Cinema", "location": "Uptown"}

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post("/api/v1/cinemas", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Cinema"
    assert data["location"] == "Uptown"
    assert "id" in data

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        list_response = await client.get("/api/v1/cinemas")

    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["name"] == "New Cinema"


@pytest.mark.asyncio
async def test_list_cinemas_returns_seeded_cinema(db_session):
    cinema = Cinema(name="Test Cinema", location="Downtown")
    db_session.add(cinema)
    await db_session.commit()
    await db_session.refresh(cinema)

    count = await db_session.scalar(select(func.count()).select_from(Cinema))
    assert count == 1, "Row was not committed to the test database"

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/api/v1/cinemas")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Cinema"
    assert data["items"][0]["location"] == "Downtown"
