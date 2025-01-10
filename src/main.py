import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from database.config import Settings
from database.db import DatabaseHelper
from models import Base

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Инициализация настроек и подключения к базе данных
settings: Settings = Settings()
db_helper = DatabaseHelper(settings.Db_settings.url, settings.Db_settings.echo)


# Асинхронный контекстный менеджер для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan started")
    try:
        async with db_helper.engine.begin() as conn:
            logger.info("Connection to the database established")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error during table creation: {e}")
        raise
    yield
    logger.info("Lifespan ended")


# Создание FastAPI приложения
app = FastAPI(lifespan=lifespan)


# Пример маршрута
@app.get("/")
async def hello_world():
    logger.info("Hello World endpoint called")
    return {"message": "Hello World"}


# Запуск приложения
if __name__ == "__main__":
    logger.info("Starting the application")
    uvicorn.run("main:app", reload=True)
