import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from database.db import database
from models import Base
from users import router as user_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan started")
    try:
        async with database.engine.begin() as conn:
            logger.info("Connection to the database established")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error during table creation: {e}")
        raise
    yield
    logger.info("Lifespan ended")


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
async def hello_world():
    logger.info("Hello World endpoint called")
    return {"message": "Hello World"}


# Запуск приложения
if __name__ == "__main__":
    logger.info("Starting the application")
    uvicorn.run("main:app", reload=True)
