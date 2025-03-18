import asyncio
import os
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from auth.dependencies import get_analytics_service
from auth.models import *  # noqa
from auth.utils import hash_password
from database import get_session
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from src.main import app

load_dotenv(".test.env", override=True)

db_name = os.getenv("POSTGRES_DB")
url = os.getenv("POSTGRES_URL")
mode = os.getenv("POSTGRES_MODE")


class MockAnalyticsService:
    def __init__(self):
        pass

    async def publish_event(self, *args, **kwargs):
        pass


@pytest_asyncio.fixture(scope="session")
async def async_engine(event_loop) -> AsyncEngine:
    engine = create_async_engine(f"{url}{db_name}", echo=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
def testing_session_maker(async_engine: AsyncEngine):
    return sessionmaker(
        async_engine,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture(autouse=True)
def mock_kafka_config(monkeypatch):
    class MockKafkaConfig:
        BOOTSTRAP_SERVERS = "localhost:9092"
        TOPIC = "test-topic"

    monkeypatch.setattr("config.KafkaConfig", MockKafkaConfig)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(async_engine):
    assert mode == "TEST"
    admin_engine = create_async_engine(
        f"{url}auth_db",
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with admin_engine.connect() as conn:
            await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)"))
            await conn.execute(text(f"CREATE DATABASE {db_name}"))
    except Exception as e:
        print(f"Ошибка при настройке базы данных: {e}")
        raise
    finally:
        await admin_engine.dispose()

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def session(testing_session_maker):
    async with testing_session_maker() as session:
        async with session.begin():
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
            await session.commit()
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def async_client(session):
    async def override_db():
        yield session

    app.dependency_overrides[get_session] = override_db  # type: ignore[attr-defined]
    app.dependency_overrides[get_analytics_service] = lambda: MockAnalyticsService()  # type: ignore[attr-defined] # noqa
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest_asyncio.fixture(scope="function")
async def user_role(session: AsyncSession):
    stmt = select(Role).where(Role.name == RoleEnum.USER.value)
    role = await session.scalar(stmt)
    if not role:
        role = Role(name=RoleEnum.USER.value)
        session.add(role)
        await session.commit()
    return role


@pytest_asyncio.fixture(scope="function")
async def admin_role(session: AsyncSession):
    stmt = select(Role).where(Role.name == RoleEnum.ADMIN.value)
    role = await session.scalar(stmt)
    if not role:
        role = Role(name=RoleEnum.ADMIN.value)
        session.add(role)
        await session.commit()
    return role


@pytest_asyncio.fixture(autouse=True)
def mock_external_services(monkeypatch):
    mock_analytics = AsyncMock()
    mock_producer = AsyncMock()
    monkeypatch.setattr("auth.service.send_confirmation_email", AsyncMock())
    monkeypatch.setattr("auth.service.send_password_reset_email", AsyncMock())
    monkeypatch.setattr("auth.analytics_service.AnalyticsService.publish_event", AsyncMock())
    monkeypatch.setattr(
        "auth.file_service.FileService.load_avatar", AsyncMock(return_value="mock_slug")
    )
    monkeypatch.setattr("auth.analytics_service.AnalyticsService", MockAnalyticsService)
    monkeypatch.setattr("auth.kafka_producer.KafkaProducer", AsyncMock())
    monkeypatch.setattr("auth.analytics_service.KafkaProducer", AsyncMock())
    monkeypatch.setattr("auth.analytics_service.AnalyticsService", mock_analytics)
    monkeypatch.setattr("auth.kafka_producer.AIOKafkaProducer", mock_producer)
    monkeypatch.setattr("auth.kafka_producer.KafkaProducer.produce_message", AsyncMock())
    yield


@pytest_asyncio.fixture(scope="function")
async def get_token_for_user(async_client: AsyncClient):
    async def _get_token(user: User):
        response = await async_client.post(
            "/api/v1/auth/users/token",
            data={"email": user.email, "password": "Password123!"},
        )
        assert response.status_code == 200
        return response.json()["access_token"]

    return _get_token


@pytest_asyncio.fixture(scope="function")
async def create_user_with_role(session: AsyncSession):
    async def _create_user(role_name: RoleEnum, is_already_exists: bool = False):
        stmt = select(Role).where(Role.name == role_name.value)
        role = await session.scalar(stmt)
        if not role:
            role = Role(name=role_name.value)
            session.add(role)
            await session.commit()

        base_username = f"{role_name.value.lower()}_user"
        base_email = f"{role_name.value.lower()}@example.com"
        if is_already_exists:
            username = "second_" + base_username
            email = "second_" + base_email
        else:
            username = base_username
            email = base_email

        user = User(
            username=username,
            email=email,
            password=hash_password("Password123!"),
            role_id=role.id,
            is_approved=True,
        )
        session.add(user)
        await session.commit()
        return user

    return _create_user


@pytest.fixture
def user_repo(session):
    return UserRepository(session)


@pytest.fixture
def role_repo(session):
    return RoleRepository(session)
