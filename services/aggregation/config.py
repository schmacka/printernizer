"""
Configuration for the usage statistics aggregation service.

Environment variables:
    DATABASE_URL: PostgreSQL or SQLite connection string
    API_KEY: Secret key for authenticating submissions
    RATE_LIMIT_PER_HOUR: Maximum submissions per installation per hour
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database configuration
    database_url: str = Field(
        default="sqlite:///./aggregation.db",
        description="Database connection URL",
        env="DATABASE_URL"
    )

    # Authentication
    api_key: str = Field(
        default="change-me-in-production",
        description="API key for authenticating submissions",
        env="API_KEY"
    )

    # Rate limiting
    rate_limit_per_hour: int = Field(
        default=10,
        description="Maximum submissions per installation per hour",
        env="RATE_LIMIT_PER_HOUR"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        env="LOG_LEVEL"
    )

    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
        env="HOST"
    )

    port: int = Field(
        default=8080,
        description="Server port",
        env="PORT"
    )

    # CORS
    allowed_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
        env="ALLOWED_ORIGINS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
