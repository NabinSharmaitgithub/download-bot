from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "testing", "production"] = Field(
        default="development",
        validation_alias="APP_ENV",
    )

    debug: bool = Field(default=False, validation_alias="DEBUG")

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )

    log_format: Literal["json", "console"] = Field(
        default="json",
        validation_alias="LOG_FORMAT",
    )

    fastapi_host: str = Field(default="0.0.0.0", validation_alias="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, validation_alias="FASTAPI_PORT")

    database_url: PostgresDsn = Field(
        validation_alias="DATABASE_URL",
    )

    database_pool_size: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, validation_alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, validation_alias="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=3600, validation_alias="DATABASE_POOL_RECYCLE")

    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")

    telegram_bot_token: str = Field(
        validation_alias="TELEGRAM_BOT_TOKEN",
        min_length=1,
    )

    bot_mode: Literal["polling", "webhook"] = Field(
        default="polling",
        validation_alias="BOT_MODE",
    )

    webhook_url: str | None = Field(default=None, validation_alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", validation_alias="WEBHOOK_PATH")
    webhook_secret: str | None = Field(default=None, validation_alias="WEBHOOK_SECRET")

    tg_max_upload_size: int = Field(default=50 * 1024 * 1024, validation_alias="TG_MAX_UPLOAD_SIZE")

    download_directory: str = Field(
        default="/data/downloads", validation_alias="DOWNLOAD_DIRECTORY"
    )
    temp_directory: str = Field(default="/tmp/downloads", validation_alias="TEMP_DIRECTORY")

    download_link_expiration: int = Field(default=3600, validation_alias="DOWNLOAD_LINK_EXPIRATION")
    download_link_hmac_secret: str = Field(
        validation_alias="DOWNLOAD_LINK_HMAC_SECRET",
        min_length=32,
    )

    max_concurrent_downloads: int = Field(default=3, validation_alias="MAX_CONCURRENT_DOWNLOADS")
    max_queue_size: int = Field(default=100, validation_alias="MAX_QUEUE_SIZE")

    cleanup_interval: int = Field(default=3600, validation_alias="CLEANUP_INTERVAL")
    temp_file_ttl: int = Field(default=86400, validation_alias="TEMP_FILE_TTL")

    admin_user_ids: list[int] = Field(default=[], validation_alias="ADMIN_USER_IDS")

    secret_key: str = Field(
        validation_alias="SECRET_KEY",
        min_length=32,
    )

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v) -> list[int]:
        if not v:
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return []

    @field_validator("webhook_url", mode="before")
    @classmethod
    def validate_webhook_url(cls, v: str | None, info) -> str | None:
        if info.data.get("bot_mode") == "webhook" and not v:
            raise ValueError("WEBHOOK_URL is required when BOT_MODE=webhook")
        return v

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_testing(self) -> bool:
        return self.app_env == "testing"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def admin_ids(self) -> list[int]:
        return self.admin_user_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()