from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings


class JWTConfig(BaseSettings):
    private_key_path: str
    public_key_path: str

    @property
    def private_key(self):
        with open(self.private_key_path, "rb") as key_file:
            return serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend(),
            )

    @property
    def public_key(self):
        with open(self.public_key_path, "rb") as key_file:
            return serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend(),
            )

    class Config:
        env_prefix = "JWT_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class BasicConfig(BaseSettings):
    url: str

    class Config:
        env_prefix = "BASE_"
        env_file = ".env"
        env_file_encoding = "utf-8"


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
    chat_id: int

    class Config:
        env_prefix = "TELEGRAM_"
        env_file = ".env"
        env_file_encoding = "utf-8"


class EmailConfig(BaseSettings):
    host: str
    port: int
    use_tls: bool
    host_user: str
    host_password: str

    class Config:
        env_prefix = "EMAIL_"
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


class VersionConfig(BaseSettings):
    api_v1_prefix: str = "/api/v1"


class AppConfig(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()
    kafka: KafkaConfig = KafkaConfig()
    telegram: TelegramConfig = TelegramConfig()
    email: EmailConfig = EmailConfig()
    basic: BasicConfig = BasicConfig()
    jwt: JWTConfig = JWTConfig()
    version: VersionConfig = VersionConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
