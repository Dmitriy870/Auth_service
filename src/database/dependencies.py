from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from database.config import Settings
from database.db import DatabaseHelper


def get_settings() -> Settings:
    return Settings()


def get_database_helper(settings: Settings = Depends(get_settings)) -> DatabaseHelper:
    return DatabaseHelper(settings.Db_settings.url, settings.Db_settings.echo)


async def get_session(
    db: DatabaseHelper = Depends(get_database_helper),
) -> AsyncSession:
    async for session in db.session_dependency():
        yield session


async def get_scoped_session_dependency(
    db: DatabaseHelper = Depends(get_database_helper),
) -> AsyncSession:
    async for session in db.scoped_session_dependency():
        yield session


def get_scoped_session(
    db: DatabaseHelper = Depends(get_database_helper),
) -> async_scoped_session:
    return db.get_scoped_session()
