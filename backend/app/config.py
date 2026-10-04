"""
Application configuration using Pydantic Settings.
All sensitive values are loaded from environment variables — never hardcoded.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Document Integrity API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/doc_integrity_db"

    # File upload
    upload_dir: str = "uploads"
    max_file_size: int = 52_428_800  # 50 MB default

    # Comma-separated MIME types
    allowed_file_types: str = (
        "application/pdf,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "image/jpeg,"
        "image/png,"
        "image/tiff,"
        "image/bmp,"
        "text/plain"
    )

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Security
    secret_key: str = "change-me-in-production"

    @property
    def allowed_file_types_list(self) -> list[str]:
        return [t.strip() for t in self.allowed_file_types.split(",")]

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def allowed_extensions(self) -> set[str]:
        return {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".txt"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
