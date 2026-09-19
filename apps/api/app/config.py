from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/app/config.py → apps/api/.env
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    env: str = "dev"
    supabase_url: str
    supabase_service_role_key: str
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()