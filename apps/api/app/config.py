"""Sozlamalar — hamma sekret env orqali (pydantic-settings). Kodda token YO'Q."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"

    bot_token: str = ""
    webhook_secret_path: str = "dev-webhook"
    webhook_secret_token: str = "dev-secret"
    webapp_url: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://manba:manba@localhost:5432/manba"
    redis_url: str = "redis://localhost:6379/0"

    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None  # localstack lokalda
    s3_bucket_pdf: str = "manba-pdf"
    s3_bucket_export: str = "manba-export"
    sqs_queue_pdf: str = "manba-pdf-tasks"

    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_daily_budget_usd: float = 10.0

    jwt_secret: str = "dev-jwt-secret-change-me"
    admin_jwt_secret: str = "dev-admin-jwt-secret"
    jwt_ttl_minutes: int = 30
    admin_access_ttl_minutes: int = 15
    admin_refresh_ttl_days: int = 7

    click_secret_key: str = ""
    payme_secret_key: str = ""

    crossref_mailto: str = "ibrohimjonovm2006@gmail.com"
    sentry_dsn: str = ""

    free_daily_sources: int = 10
    free_daily_pdf: int = 1
    free_pdf_max_mb: int = 5
    pdf_max_mb: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
