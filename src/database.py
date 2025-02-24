from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DBSettings
from repositories.uow import UnitOfWork


class DatabaseHelper:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, url: str, echo: bool = False):
        if self._initialized:
            return

        self.engine = create_async_engine(url=url, echo=echo)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            autocommit=False,
        )

        self._initialized = True

    async def session_dependency(self):
        async with self.session_factory() as session:
            yield session
            await session.close()


def get_settings() -> DBSettings:
    return DBSettings()


def get_database_helper(settings: Annotated[DBSettings, Depends(get_settings)]) -> DatabaseHelper:
    return DatabaseHelper(url=str(settings.URL), echo=settings.ECHO)


async def get_session(db: Annotated[DatabaseHelper, Depends(get_database_helper)]) -> AsyncSession:
    async with db.session_factory() as session:
        yield session


async def get_unit_of_work(session: Annotated[AsyncSession, Depends(get_session)]) -> UnitOfWork:
    async with UnitOfWork(session) as uow:
        yield uow
