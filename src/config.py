from cryptography.fernet import Fernet
from pydantic import Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings


class JWTConfig(BaseSettings):
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE: int = Field(default=60)

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


class EncryptionConfig(BaseSettings):
    KEY: str = Field(...)

    @validator("KEY")
    def validate_key(cls, value: str) -> bytes:
        try:
            key_bytes = value.encode()
            Fernet(key_bytes)
            return key_bytes
        except Exception as e:
            raise ValueError(f"Invalid Fernet key: {e}")

    class Config:
        env_prefix = "ENCRYPTION_"
        case_sensitive = False


class FileConfig(BaseSettings):
    BASE_URL: str = Field(...)
    UPLOAD_URL: str = Field(...)
    DELETE_URL: str = Field(...)

    class Config:
        env_prefix = "FILE_"
