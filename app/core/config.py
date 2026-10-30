"""Environment based application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables and an optional local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DocuDialog"
    environment: str = "local"
    local_user_email: str = "developer@local.test"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)
    database_url: str | None = None
    upload_directory: Path = Path("storage/uploads")


@lru_cache
def get_settings() -> Settings:
    """Return one settings instance so app components share the same configuration."""

    return Settings()
