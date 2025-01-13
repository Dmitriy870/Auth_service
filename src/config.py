from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class JWTConfig(BaseSettings):
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)

    class Config:
        env_prefix = "JWT_"


class BasicConfig(BaseSettings):
    URL: str = Field(...)

    class Config:
        env_prefix = "BASE_"


class RedisConfig(BaseSettings):
    URL: RedisDsn = Field(...)
    HOST: str = Field(...)
    PORT: int = Field(...)
    DB: int = Field(...)

    class Config:
        env_prefix = "REDIS_"


class KafkaConfig(BaseSettings):
    BOOTSTRAP_SERVERS: str = Field(...)

    class Config:
        env_prefix = "KAFKA_"


class TelegramConfig(BaseSettings):
    TOKEN: str = Field(...)
    CHAT_ID: int = Field(...)

    class Config:
        env_prefix = "TELEGRAM_"


class EmailConfig(BaseSettings):
    HOST: str = Field(...)
    PORT: int = Field(...)
    USE_TLS: bool = Field(...)
    HOST_USER: str = Field(...)
    HOST_PASSWORD: str = Field(...)

    class Config:
        env_prefix = "EMAIL_"


class PostgresConfig(BaseSettings):
    DB: str = Field(...)
    USER: str = Field(...)
    PASSWORD: str = Field(...)
    HOST: str = Field(...)
    PORT: int = Field(...)
    URL: PostgresDsn = Field(...)

    class Config:
        env_prefix = "POSTGRES_"


class VersionConfig(BaseSettings):
    API_V1_PREFIX: str = Field(default="/api/v1")


class DBSettings(PostgresConfig):
    ECHO: bool = True
