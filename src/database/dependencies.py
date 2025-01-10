# dependencies.py
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from database.config import Settings
from database.db import DatabaseHelper


# Зависимость для получения настроек
def get_settings() -> Settings:
    return Settings()


# Зависимость для получения DatabaseHelper
def get_database(settings: Settings = Depends(get_settings)) -> DatabaseHelper:
    return DatabaseHelper(settings.Db_settings.url, settings.Db_settings.echo)


# Зависимость для обычной сессии
async def get_session(
    db: DatabaseHelper = Depends(get_database),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in db.session_dependency():
        yield session


# Зависимость для scoped-сессии
async def get_scoped_session_dependency(
    db: DatabaseHelper = Depends(get_database),
) -> AsyncGenerator[AsyncSession, None]:
    async for session in db.scoped_session_dependency():
        yield session


# Зависимость для получения async_scoped_session напрямую
def get_scoped_session(
    db: DatabaseHelper = Depends(get_database),
) -> async_scoped_session:
    return db.get_scoped_session()
