"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables or a .env file.
This ensures no secrets are hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Bulk Certificate Generator API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db",
        description="PostgreSQL connection string"
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db_test",
        description="Test PostgreSQL connection string"
    )

    # File Storage
    CERTIFICATE_OUTPUT_DIR: str = Field(
        default="generated_certificates",
        description="Directory where generated PDFs are stored"
    )

    # Validation limits
    MAX_RECIPIENTS_PER_JOB: int = Field(
        default=1000,
        description="Maximum recipients allowed per job"
    )
    MAX_STRING_LENGTH: int = Field(
        default=255,
        description="Maximum string length for text fields"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()

# Ensure output directory exists
os.makedirs(settings.CERTIFICATE_OUTPUT_DIR, exist_ok=True)
