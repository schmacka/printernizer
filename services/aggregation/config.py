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

    # SMTP Email Configuration
    smtp_enabled: bool = Field(
        default=False,
        description="Enable SMTP email functionality",
        env="SMTP_ENABLED"
    )

    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server hostname",
        env="SMTP_HOST"
    )

    smtp_port: int = Field(
        default=587,
        description="SMTP server port (587 for TLS, 465 for SSL)",
        env="SMTP_PORT"
    )

    smtp_username: str = Field(
        default="",
        description="SMTP authentication username",
        env="SMTP_USERNAME"
    )

    smtp_password: str = Field(
        default="",
        description="SMTP authentication password",
        env="SMTP_PASSWORD"
    )

    smtp_from_email: str = Field(
        default="",
        description="Email address to send from",
        env="SMTP_FROM_EMAIL"
    )

    smtp_from_name: str = Field(
        default="Printernizer Stats",
        description="Display name for sent emails",
        env="SMTP_FROM_NAME"
    )

    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS encryption (STARTTLS)",
        env="SMTP_USE_TLS"
    )

    smtp_use_ssl: bool = Field(
        default=False,
        description="Use SSL encryption (direct SSL)",
        env="SMTP_USE_SSL"
    )

    # Report Recipients
    report_recipients: list[str] = Field(
        default=[],
        description="Email addresses to receive reports",
        env="REPORT_RECIPIENTS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
