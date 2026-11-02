"""Environment based application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
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
    environment: str = "production"
    local_user_email: str = "developer@local.test"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=list)
    database_url: str | None = None
    upload_directory: Path = Path("storage/uploads")
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    max_upload_total_bytes: int = Field(default=50 * 1024 * 1024, gt=0)
    max_upload_files: int = Field(default=10, gt=0)
    openai_api_key: SecretStr | None = None
    embedding_model: str = "text-embedding-3-small"
    max_ingestion_attempts: int = Field(default=3, gt=0)
    ingestion_poll_seconds: float = Field(default=2.0, gt=0)
    ingestion_stale_after_seconds: int = Field(default=1800, gt=0)
    chunk_size: int = Field(default=1000, gt=0)
    chunk_overlap: int = Field(default=150, ge=0)

    @model_validator(mode="after")
    def validate_chunk_configuration(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one settings instance so app components share the same configuration."""

    return Settings()
