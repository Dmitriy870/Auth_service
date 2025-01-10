from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.config import AppConfig

config = AppConfig()


class DBSettings(BaseModel):
    url: str = str(config.postgres.url)
    echo: bool = True


class Settings(BaseSettings):
    api_v1_prefix: str = "api/v1/"
    Db_settings: DBSettings = DBSettings()
