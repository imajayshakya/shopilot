"""Shopilot API — Application configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    app_name: str = "Shopilot"
    app_version: str = "0.1.0"
    debug: bool = False

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./shopilot.db"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Azure OpenAI ---
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-06-01"

    # --- Auth ---
    jwt_secret: str = "change-this-to-a-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # --- Rate Limiting ---
    rate_limit_anonymous: int = 10
    rate_limit_authenticated: int = 100

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def ai_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)


settings = Settings()
