"""
Application configuration using Pydantic settings.

Loads configuration from environment variables.
"""
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://mybudget:mybudget@localhost:5432/mybudget",
        description="PostgreSQL database URL (must use asyncpg driver)",
    )

    # Security
    SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for session signing (generate with: openssl rand -hex 32)",
    )
    ALGORITHM: str = Field(default="HS256", description="Algorithm for token signing")
    SESSION_LIFETIME_MINUTES: int = Field(
        default=30, ge=1, le=1440, description="Session lifetime in minutes"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Frontend URL (for CORS)
    FRONTEND_URL: str = Field(
        default="http://localhost:5173", description="Frontend URL for CORS configuration"
    )

    # API Configuration
    API_V1_PREFIX: str = Field(default="/api", description="API v1 route prefix")


# Global settings instance
settings = Settings()
