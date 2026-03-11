from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")
    storage_dir: str = Field(default="/app/storage", alias="STORAGE_DIR")
    temp_dir: str = Field(default="/app/storage/tmp", alias="TEMP_DIR")
    output_dir: str = Field(default="/app/storage/jobs", alias="OUTPUT_DIR")

    max_upload_mb: int = Field(default=100, alias="MAX_UPLOAD_MB")
    allowed_origins_raw: str = Field(
        default="http://localhost:3000,http://localhost:3001", alias="ALLOWED_ORIGINS"
    )

    api_key: str | None = Field(default=None, alias="API_KEY")

    demucs_model: str = Field(default="htdemucs", alias="DEMUCS_MODEL")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
