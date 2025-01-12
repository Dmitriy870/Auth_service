from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import AppConfig
from database.dependencies import get_database_helper, get_settings
from models.models import Base
from users import router as users_router

config = AppConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_database_helper(settings)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(users_router, prefix=config.version.api_v1_prefix)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
