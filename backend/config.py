"""
Application configuration via environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM Provider API Keys ---
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    # --- Default LLM Settings ---
    default_model: str = "openrouter/anthropic/claude-sonnet-4.6"
    default_provider: str = "openrouter"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/inference_logger"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # --- Features ---
    pii_redaction_enabled: bool = True
    context_window_size: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def available_providers(self) -> list[str]:
        """Return list of providers that have API keys configured."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.google_api_key:
            providers.append("google")
        if self.deepseek_api_key:
            providers.append("deepseek")
        if self.openrouter_api_key:
            providers.append("openrouter")
        return providers

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Sync to os.environ for litellm
import os
if settings.openai_api_key: os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.anthropic_api_key: os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
if settings.google_api_key: os.environ["GEMINI_API_KEY"] = settings.google_api_key
if settings.deepseek_api_key: os.environ["DEEPSEEK_API_KEY"] = settings.deepseek_api_key
if settings.openrouter_api_key: os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key
