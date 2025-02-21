import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from auth.logging_conf import configurate_logging
from auth.router import router as auth_router
from config import VersionConfig
from containers.file_config import FileConfigContainer
from containers.kafka import KafkaContainer

logger = configurate_logging(logging.INFO)
version_config = VersionConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = KafkaContainer()
    container.wire(modules=["auth.kafka_producer"])
    logger.info("Containers successfully  initialized")
    file_container = FileConfigContainer()
    file_container.wire(modules=["auth.file_service"])
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix=version_config.API_V1_PREFIX)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
