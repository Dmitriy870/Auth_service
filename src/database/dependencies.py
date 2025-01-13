from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import DBSettings
from database.db import DatabaseHelper


def get_settings() -> DBSettings:
    return DBSettings()


def get_database_helper(settings: Annotated[DBSettings, Depends(get_settings)]) -> DatabaseHelper:
    return DatabaseHelper(url=str(settings.URL), echo=settings.ECHO)


async def get_session(db: Annotated[DatabaseHelper, Depends(get_database_helper)]) -> AsyncSession:
    async for session in db.session_dependency():
        yield session
