from pydantic import BaseModel
from pydantic_settings import BaseSettings

from config import AppConfig

config = AppConfig()


class DBSettings(BaseModel):
    url: str = str(config.postgres.url)
    echo: bool = True


class Settings(BaseSettings):
    Db_settings: DBSettings = DBSettings()
