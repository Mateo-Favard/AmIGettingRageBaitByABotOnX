from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Environment ---
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = False

    # --- Secrets ---
    secret_key: SecretStr = SecretStr("change-me-in-production")
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://amirb:change_me_in_production@db:5432/amirb_db"
    )
    redis_url: str = "redis://redis:6379/0"
    twitter_api_key: SecretStr = SecretStr("")

    # --- Twitter Credentials (Twikit, gratuit) ---
    twitter_username: SecretStr = SecretStr("")
    twitter_email: SecretStr = SecretStr("")
    twitter_password: SecretStr = SecretStr("")

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v  # type: ignore[return-value]

    # --- Analysis ---
    analysis_cache_ttl_seconds: int = 604_800  # 7 days

    # --- Twitter API ---
    twitter_api_timeout_seconds: int = 10
    twitter_api_max_retries: int = 3

    # --- Rate Limiting ---
    rate_limit_analyze: str = "10/minute"
    rate_limit_global: str = "100/minute"

    # --- ML ---
    ml_inference_timeout_seconds: int = 300
    ml_per_analyzer_timeout_seconds: float = 120.0
    ml_models_path: str = "models"

    # --- AI Content sub-strategies ---
    ai_content_statistical_enabled: bool = True
    ai_content_cross_tweet_enabled: bool = True
    ai_content_strategy_timeout_seconds: float = 45.0

    @model_validator(mode="after")
    def validate_no_debug_in_production(self) -> "Settings":
        if self.environment == "production" and self.debug:
            msg = "debug=True is forbidden in production"
            raise ValueError(msg)
        return self

    @property
    def has_twitter_credentials(self) -> bool:
        return all(
            v.get_secret_value()
            for v in [
                self.twitter_username,
                self.twitter_email,
                self.twitter_password,
            ]
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
