from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://fuels_user:fuels_password@localhost:5432/fuels_logistics_db"

    # Anthropic API
    anthropic_api_key: str = ""

    # Gmail SMTP Configuration
    gmail_user: str = ""  # Gmail address for sending emails
    gmail_app_password: str = ""  # Gmail app password (not regular password)
    gmail_enabled: bool = False  # Set to True to enable real email sending

    # Coordinator
    coordinator_email: str = ""  # CC address for escalation replies to carriers

    # Application
    debug: bool = True
    log_level: str = "INFO"

    # Agent Settings
    agent_check_interval_minutes: int = 15
    default_runout_threshold_hours: float = 48.0
    critical_runout_threshold_hours: float = 24.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
