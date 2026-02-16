from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://fuels_user:fuels_password@localhost:5432/fuels_logistics_db"

    # Anthropic API
    anthropic_api_key: str = ""

    # SendGrid Email Configuration (HTTP API — works on Railway)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@fuelslogistics.com"
    sendgrid_from_name: str = "Fuels Logistics AI Coordinator"

    # Gmail IMAP (inbound email polling only — NOT used for sending)
    gmail_user: str = ""
    gmail_app_password: str = ""

    # Coordinator
    coordinator_email: str = ""  # CC address for escalation replies to carriers

    # Application
    debug: bool = True
    log_level: str = "INFO"

    # CORS - comma-separated allowed origins for production
    cors_origins: str = ""

    # Agent Settings
    agent_check_interval_minutes: int = 15
    default_runout_threshold_hours: float = 48.0
    critical_runout_threshold_hours: float = 24.0

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        # Railway injects postgres:// but SQLAlchemy 2.0 requires postgresql://
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
