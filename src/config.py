from typing import Optional

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class RedisConfig(BaseSettings):
    url: RedisDsn
    host: str
    port: int
    db: int

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class KafkaConfig(BaseSettings):
    bootstrap_servers: str

    class Config:
        env_prefix = "KAFKA_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class TelegramConfig(BaseSettings):
    token: str
    chat_id: Optional[int]

    class Config:
        env_prefix = "TELEGRAM_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class PostgresConfig(BaseSettings):
    db: str
    user: str
    password: str
    host: str
    port: int
    url: PostgresDsn

    class Config:
        env_prefix = "POSTGRES_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class AppConfig(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    kafka: KafkaConfig = KafkaConfig()
    telegram: TelegramConfig = TelegramConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
