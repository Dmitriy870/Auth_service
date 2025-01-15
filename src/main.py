from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from auth.router import router as auth_router
from config import VersionConfig
from database import get_database_helper, get_settings
from models import Base

version_config = VersionConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_database_helper(settings)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix=version_config.API_V1_PREFIX)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
