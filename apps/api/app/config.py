from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    env: str = "dev"
    supabase_url: str
    supabase_service_role_key: str
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]
    gemini_api_key: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()