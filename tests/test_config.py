import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    def test_default_values(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)

        settings = Settings()

        assert settings.app_env == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.fastapi_host == "0.0.0.0"
        assert settings.fastapi_port == 8000
        assert settings.database_pool_size == 10
        assert settings.max_concurrent_downloads == 3
        assert settings.cleanup_interval == 3600

    def test_admin_ids_parsing(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("ADMIN_USER_IDS", "123, 456, 789")

        settings = Settings()
        assert settings.admin_ids == [123, 456, 789]

    def test_admin_ids_empty(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("ADMIN_USER_IDS", "")

        settings = Settings()
        assert settings.admin_ids == []

    def test_webhook_url_required_when_webhook_mode(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("BOT_MODE", "webhook")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "WEBHOOK_URL is required when BOT_MODE=webhook" in str(exc_info.value)

    def test_secret_key_min_length(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)

        with pytest.raises(ValidationError):
            Settings()

    def test_hmac_secret_min_length(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "short")

        with pytest.raises(ValidationError):
            Settings()

    def test_is_development_property(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("APP_ENV", "development")

        settings = Settings()
        assert settings.is_development is True
        assert settings.is_testing is False
        assert settings.is_production is False

    def test_is_testing_property(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("APP_ENV", "testing")

        settings = Settings()
        assert settings.is_testing is True

    def test_is_production_property(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("DOWNLOAD_LINK_HMAC_SECRET", "b" * 32)
        monkeypatch.setenv("APP_ENV", "production")

        settings = Settings()
        assert settings.is_production is True