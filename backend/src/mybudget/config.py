"""
Application configuration using Pydantic settings.

Loads configuration from environment variables.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database - use str type to allow flexibility with driver prefixes
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://mybudget:mybudget@localhost:5432/mybudget",
        description="PostgreSQL database URL",
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        """Ensure the database URL uses an async driver."""
        # Convert postgresql:// to postgresql+psycopg:// for async support
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v

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

    # GoCardless Bank Account Data API
    GOCARDLESS_SECRET_ID: str | None = Field(
        default=None,
        description="GoCardless Bank Account Data API secret ID",
    )
    GOCARDLESS_SECRET_KEY: str | None = Field(
        default=None,
        description="GoCardless Bank Account Data API secret key",
    )
    GOCARDLESS_BASE_URL: str = Field(
        default="https://bankaccountdata.gocardless.com/api/v2",
        description="GoCardless Bank Account Data API base URL",
    )

    # Bank Token Encryption
    BANK_TOKEN_ENCRYPTION_KEY: str | None = Field(
        default=None,
        description="Fernet key for encrypting bank tokens (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')",
    )


# Global settings instance
settings = Settings()
