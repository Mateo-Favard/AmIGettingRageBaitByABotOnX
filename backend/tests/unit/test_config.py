import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove env vars that leak from Docker into unit tests."""
    for key in (
        "DEBUG",
        "ENVIRONMENT",
        "SECRET_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "TWITTER_API_KEY",
        "CORS_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)


class TestSettings:
    def test_default_settings(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            secret_key="test",  # type: ignore[arg-type]
            database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
            twitter_api_key="key",  # type: ignore[arg-type]
        )
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.analysis_cache_ttl_seconds == 604_800

    def test_debug_forbidden_in_production(self) -> None:
        with pytest.raises(ValidationError, match="debug=True is forbidden"):
            Settings(
                _env_file=None,  # type: ignore[call-arg]
                environment="production",
                debug=True,
                secret_key="test",  # type: ignore[arg-type]
                database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
                twitter_api_key="key",  # type: ignore[arg-type]
            )

    def test_debug_allowed_in_development(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            environment="development",
            debug=True,
            secret_key="test",  # type: ignore[arg-type]
            database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
            twitter_api_key="key",  # type: ignore[arg-type]
        )
        assert settings.debug is True

    def test_secret_str_not_exposed(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            secret_key="super-secret",  # type: ignore[arg-type]
            database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
            twitter_api_key="api-key",  # type: ignore[arg-type]
        )
        assert "super-secret" not in repr(settings)
        assert "api-key" not in repr(settings)

    def test_is_production_property(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            environment="production",
            secret_key="test",  # type: ignore[arg-type]
            database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
            twitter_api_key="key",  # type: ignore[arg-type]
        )
        assert settings.is_production is True

    def test_cors_origins_parses_comma_separated(self) -> None:
        settings = Settings(
            _env_file=None,  # type: ignore[call-arg]
            secret_key="test",  # type: ignore[arg-type]
            database_url="postgresql+asyncpg://u:p@localhost/db",  # type: ignore[arg-type]
            twitter_api_key="key",  # type: ignore[arg-type]
            cors_origins="http://localhost:3000,http://localhost:8080",  # type: ignore[arg-type]
        )
        assert settings.cors_origins == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]
