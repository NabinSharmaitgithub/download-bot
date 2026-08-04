import json
import logging
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
import structlog

from app.core.logging import filter_secrets, get_logger, setup_logging


class TestLogging:
    def test_setup_logging_json_format(self, monkeypatch):
        monkeypatch.setenv("LOG_FORMAT", "json")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        with patch("app.core.logging.get_settings") as mock_settings:
            mock_settings.return_value.log_format = "json"
            mock_settings.return_value.log_level = "DEBUG"
            mock_settings.return_value.app_env = "testing"

            setup_logging()

            logger = get_logger("test")
            logger.info("test_message", key="value")

    def test_setup_logging_console_format(self, monkeypatch):
        monkeypatch.setenv("LOG_FORMAT", "console")
        monkeypatch.setenv("LOG_LEVEL", "INFO")

        with patch("app.core.logging.get_settings") as mock_settings:
            mock_settings.return_value.log_format = "console"
            mock_settings.return_value.log_level = "INFO"
            mock_settings.return_value.app_env = "testing"

            setup_logging()

            logger = get_logger("test")
            logger.info("test_message", key="value")

    def test_filter_secrets_redacts_sensitive_fields(self):
        event_dict = {
            "message": "test",
            "token": "secret123",
            "password": "pass123",
            "api_key": "key123",
            "normal_field": "value",
        }

        result = filter_secrets(None, "info", event_dict)

        assert result["token"] == "***REDACTED***"
        assert result["password"] == "***REDACTED***"
        assert result["api_key"] == "***REDACTED***"
        assert result["normal_field"] == "value"

    def test_filter_secrets_case_insensitive(self):
        event_dict = {
            "TOKEN": "secret",
            "PASSWORD": "pass",
            "API_KEY": "key",
            "Secret_Key": "value",
        }

        result = filter_secrets(None, "info", event_dict)

        assert result["TOKEN"] == "***REDACTED***"
        assert result["PASSWORD"] == "***REDACTED***"
        assert result["API_KEY"] == "***REDACTED***"
        assert result["Secret_Key"] == "***REDACTED***"

    def test_get_logger_returns_bound_logger(self):
        logger = get_logger("test_module")
        assert isinstance(logger, structlog.stdlib.BoundLogger)