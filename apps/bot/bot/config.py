"""Bot sozlamalari — env orqali."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    bot_mode: str = "webhook"  # webhook | polling (lokal)
    webhook_base: str = "https://api.loyiha.uz"
    webhook_secret_path: str = "dev-webhook"
    webhook_secret_token: str = "dev-secret"
    api_base_url: str = "http://localhost:8000"
    webapp_url: str = "https://webapp.loyiha.uz"
    redis_url: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()
